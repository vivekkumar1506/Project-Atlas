import logging
import time
from pathlib import Path
from typing import Any, Dict, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.app.config import get_settings

logger = logging.getLogger("atlas.db")
settings = get_settings()

Base = declarative_base()

# SQLAlchemy engine with connection pooling and health pre-ping
engine = create_engine(
    settings.database_url,
    pool_size=settings.mysql_pool_size,
    pool_recycle=settings.mysql_pool_recycle,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Dict[str, Any]:
    """Test database connectivity safely without exposing passwords or credentials."""
    start_time = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "connected": True,
            "database": settings.mysql_database,
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        # Safe sanitized error message without credentials
        error_msg = str(exc)
        if settings.mysql_password and settings.mysql_password in error_msg:
            error_msg = error_msg.replace(settings.mysql_password, "******")
        logger.error(f"Database connection check failed: {error_msg}")
        return {
            "connected": False,
            "database": settings.mysql_database,
            "latency_ms": latency_ms,
            "error": "Failed to connect to MySQL database",
        }


def init_database_and_schema(schema_file_path: Path = None) -> bool:
    """Ensure database exists and execute schema DDL if not already created."""
    if schema_file_path is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        schema_file_path = base_dir / "database" / "schema.sql"

    logger.info("Initializing MySQL database and schema...")
    try:
        # Step 1: Connect to server level to ensure database exists
        server_engine = create_engine(
            settings.server_database_url,
            isolation_level="AUTOCOMMIT",
        )
        with server_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` "
                    f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            )
        server_engine.dispose()

        # Step 2: Read and execute schema statements
        if not schema_file_path.exists():
            logger.warning(f"Schema file not found at {schema_file_path}")
            return False

        with open(schema_file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # Split SQL into individual statements by semicolon
        # avoiding comments
        statements = []
        current_stmt = []
        for line in sql_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("--") or not stripped:
                continue
            current_stmt.append(line)
            if stripped.endswith(";"):
                stmt = "\n".join(current_stmt).strip()
                if stmt:
                    statements.append(stmt)
                current_stmt = []

        with engine.connect() as conn:
            for statement in statements:
                if statement:
                    conn.execute(text(statement))
            conn.commit()

        logger.info("Database and schema successfully initialized.")
        return True
    except Exception as exc:
        safe_msg = str(exc)
        if settings.mysql_password and settings.mysql_password in safe_msg:
            safe_msg = safe_msg.replace(settings.mysql_password, "******")
        logger.error(f"Schema initialization error: {safe_msg}")
        raise
