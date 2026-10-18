import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.chat import router as chat_router
from backend.app.api.health import router as health_router
from backend.app.api.ingest import router as ingest_router
from backend.app.config import get_settings
from backend.app.services.db import check_db_connection, init_database_and_schema

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("atlas.main")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info(f"Starting {settings.app_name} (version {settings.app_version})")
    logger.info(f"Environment: {settings.environment}")

    # Check and initialize MySQL database schema on startup
    try:
        init_database_and_schema()
        health = check_db_connection()
        if health.get("connected"):
            logger.info(f"Database connection verified (latency: {health.get('latency_ms')}ms)")
        else:
            logger.warning(f"Database connection degraded: {health.get('error')}")
    except Exception as exc:
        logger.error(f"Error during database initialization: {exc}")

    yield

    logger.info("Project Atlas backend service shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend AI API for Project Atlas Market Research Report Copilot.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for local development and CodeIgniter portal integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(ingest_router)
app.include_router(ingest_router, prefix="/api/v1")
app.include_router(chat_router)
app.include_router(chat_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root_status():
    """Welcome endpoint providing service metadata."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.environment == "development"),
    )
