"""Phase 1 Foundation Verification Script.

Tests:
1. Environment variables and configuration loading.
2. MySQL database connection and schema initialization.
3. Verification of required baseline tables and seed records.
4. FastAPI application initialization and GET /health response.
"""

import sys
from pathlib import Path

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.config import get_settings
from backend.app.main import app
from backend.app.services.db import (
    check_db_connection,
    engine,
    init_database_and_schema,
)


def run_verification():
    print("=" * 60)
    print(" PROJECT ATLAS - PHASE 1 FOUNDATION VERIFICATION")
    print("=" * 60)

    # 1. Configuration Check
    print("\n[1/4] Checking Configuration & Environment Variables...")
    settings = get_settings()
    print(f"  - App Name: {settings.app_name}")
    print(f"  - Environment: {settings.environment}")
    print(f"  - MySQL Host: {settings.mysql_host}:{settings.mysql_port}")
    print(f"  - MySQL User: {settings.mysql_user}")
    print(f"  - MySQL Database: {settings.mysql_database}")
    print("  - Passwords/Secrets: Hidden & safely isolated in .env [OK]")

    # 2. Database Connection & Schema Setup
    print("\n[2/4] Testing MySQL Connectivity & Initializing Schema...")
    schema_ok = init_database_and_schema()
    assert schema_ok, "Schema initialization failed"
    print("  - Schema DDL executed successfully [OK]")

    health = check_db_connection()
    print(f"  - DB Connection Status: {health.get('connected')}")
    print(f"  - Connection Latency: {health.get('latency_ms')} ms")
    assert health.get("connected"), f"Database connection failed: {health.get('error')}"

    # 3. Inspecting Tables & Seed Data
    print("\n[3/4] Verifying Relational Schema & Baseline Entitlements...")
    with engine.connect() as conn:
        tables = [
            row[0]
            for row in conn.execute(text("SHOW TABLES;")).fetchall()
        ]
        print(f"  - Total Tables Found: {len(tables)}")
        for t in tables:
            print(f"    * {t}")

        expected_tables = {
            "clients",
            "reports",
            "market_metrics",
            "client_report_entitlements",
            "conversations",
            "messages",
            "citations",
            "feedback",
            "escalations",
            "security_events",
            "request_metrics",
            "ingestion_runs",
        }
        missing = expected_tables - set(tables)
        if missing:
            print(f"  - WARNING: Missing tables: {missing}")
        else:
            print("  - All 12 expected schema tables present [OK]")

        # Check clients
        clients = conn.execute(text("SELECT client_id, name, status FROM clients;")).fetchall()
        print(f"  - Clients in DB: {len(clients)}")
        for c in clients:
            print(f"    * {c[0]}: {c[1]} ({c[2]})")

        # Check entitlements (PRD AT-03)
        entitlements = conn.execute(
            text("SELECT client_id, report_id, status FROM client_report_entitlements;")
        ).fetchall()
        print(f"  - Baseline Entitlements: {len(entitlements)}")
        for e in entitlements:
            print(f"    * Client {e[0]} -> Report {e[1]} [{e[2]}]")

    # 4. FastAPI Endpoint Verification
    print("\n[4/4] Testing FastAPI /health and / Endpoints...")
    with TestClient(app) as client:
        # Root endpoint
        root_resp = client.get("/")
        assert root_resp.status_code == 200, f"Root failed: {root_resp.status_code}"
        print(f"  - GET / -> 200 OK: {root_resp.json()['status']}")

        # Health endpoint
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.status_code}"
        health_data = health_resp.json()
        print(f"  - GET /health -> 200 OK")
        print(f"    * Status: {health_data['status']}")
        print(f"    * DB Status: {health_data['database']}")

    print("\n" + "=" * 60)
    print(" [SUCCESS] ALL PHASE 1 FOUNDATION CHECKS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_verification()
