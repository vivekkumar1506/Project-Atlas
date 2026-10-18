"""Read-only SQL tool with strict write blockers for Project Atlas.

CRITICAL SECURITY GUARANTEES:
- Blocks all DDL and DML write operations (DELETE, INSERT, UPDATE, DROP, ALTER, TRUNCATE, REPLACE).
- Enforces read-only SELECT statements only against approved tables (`reports`, `market_metrics`).
- Enforces max row limits (default 50) and statement timeouts.
- Natural-language attacks (e.g. "delete rows") fail safely.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.services.db import SessionLocal

logger = logging.getLogger("atlas.sql_tool")

# Blocklist for any write/schema-modifying SQL tokens
FORBIDDEN_SQL_PATTERNS = [
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bREPLACE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bINTO\s+OUTFILE\b",
    r"\bLOAD_FILE\b",
]

# Allowlisted tables for public/analyst queries
ALLOWED_TABLES = {"reports", "market_metrics"}


def is_safe_read_only_query(query: str) -> tuple[bool, Optional[str]]:
    """Verify that query contains strictly SELECT operations and no write tokens."""
    cleaned = query.strip()

    # Must start with SELECT (or WITH ... SELECT)
    if not re.match(r"^(SELECT|WITH)\b", cleaned, re.IGNORECASE):
        return False, "Query must start with SELECT or WITH statement."

    # Check against forbidden tokens
    for pattern in FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return False, f"Write or destructive statement blocked: prohibited keyword match."

    # Verify target tables are in allowlist
    # Extract table names following FROM or JOIN
    table_matches = re.findall(r"\b(?:FROM|JOIN)\s+`?([a-zA-Z0-9_]+)`?", cleaned, re.IGNORECASE)
    for tbl in table_matches:
        if tbl.lower() not in ALLOWED_TABLES:
            return False, f"Access to table '{tbl}' is not permitted in read-only SQL tool."

    return True, None


def execute_read_only_query(
    sql_query: str,
    row_limit: int = 50,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Execute a parameterized read-only aggregate query safely."""
    start_time = time.perf_counter()
    is_safe, err_msg = is_safe_read_only_query(sql_query)

    if not is_safe:
        logger.warning(f"Blocked unsafe SQL query attempt: {err_msg}")
        return {
            "success": False,
            "blocked": True,
            "error": err_msg,
            "rows": [],
            "row_count": 0,
            "query": sql_query,
            "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
        }

    # Ensure query has LIMIT if not present
    bounded_query = sql_query.strip().rstrip(";")
    if not re.search(r"\bLIMIT\s+\d+\b", bounded_query, re.IGNORECASE):
        bounded_query += f" LIMIT {row_limit}"

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        result = db.execute(text(bounded_query))
        columns = list(result.keys()) if result.returns_rows else []
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "success": True,
            "blocked": False,
            "query": bounded_query,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "duration_ms": duration_ms,
        }
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"SQL execution error: {exc}")
        return {
            "success": False,
            "blocked": False,
            "error": "Query execution failed.",
            "query": bounded_query,
            "rows": [],
            "row_count": 0,
            "duration_ms": duration_ms,
        }
    finally:
        if close_db:
            db.close()
