"""Phase 2 Verification Script: Ingestion and Access-Aware RAG.

Tests:
1. Ingestion of all 6 reports into ChromaDB with metadata.
2. Ingestion tracking in MySQL `ingestion_runs` and `reports` status.
3. Entitlement Filtering Security Boundary (PRD AT-03):
   - Client C-01 can access R-101 (paid) + R-102 (public excerpt) + R-103 (paid).
   - Client C-02 can access R-102 (public excerpt) + R-103 (paid).
   - VERIFY that C-02 CANNOT retrieve any chunk from R-101 (zero leakage).
4. Prompt Injection Preservation:
   - Ensure R-102 Page 14 contains the attack footnote in vector store without executing it.
5. Ingest API endpoint POST /ingest verification with X-API-Key.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.config import get_settings
from backend.app.main import app
from backend.app.rag.ingestion import ingest_all_reports
from backend.app.rag.retriever import (
    get_client_allowed_report_ids,
    retrieve_entitled_chunks,
)
from backend.app.rag.vector_store import get_reports_collection
from backend.app.services.db import engine


def run_phase2_verification():
    print("=" * 65)
    print(" PROJECT ATLAS - PHASE 2 INGESTION & ACCESS-AWARE RAG")
    print("=" * 65)
    settings = get_settings()

    # Step 1: Run Ingestion
    print("\n[1/5] Ingesting all market reports from reports/ directory...")
    ingest_results = ingest_all_reports()
    print(f"  - Total Reports Processed: {len(ingest_results)}")
    for res in ingest_results:
        print(f"    * {res['report_id']}: {res.get('chunks_count', 0)} chunks [{res['status']}]")
        assert res["status"] == "success", f"Ingestion failed for {res['report_id']}"

    # Step 2: Vector DB Collection Verification
    print("\n[2/5] Inspecting ChromaDB Vector Store...")
    collection = get_reports_collection()
    total_docs = collection.count()
    print(f"  - Total Chunks Indexed in ChromaDB: {total_docs}")
    assert total_docs > 0, "No chunks found in vector database!"

    # Step 3: MySQL Ingestion Runs Tracking
    print("\n[3/5] Verifying MySQL ingestion_runs and reports status...")
    with engine.connect() as conn:
        runs = conn.execute(
            text("SELECT run_id, report_id, status, chunks_count FROM ingestion_runs ORDER BY started_at DESC LIMIT 6;")
        ).fetchall()
        print(f"  - Recent MySQL Ingestion Runs: {len(runs)}")
        for r in runs:
            print(f"    * {r[1]} -> status: {r[2]}, chunks: {r[3]} (run: {r[0]})")
            assert r[2] == "completed", f"Run {r[0]} was not completed"

        ingested_reports = conn.execute(
            text("SELECT report_id, ingestion_status FROM reports WHERE ingestion_status = 'ingested';")
        ).fetchall()
        print(f"  - Reports with status 'ingested' in MySQL: {len(ingested_reports)}")
        assert len(ingested_reports) >= 6, "Not all reports updated to 'ingested' in MySQL"

    # Step 4: CRITICAL SECURITY TEST - Pre-LLM Entitlement Filtering (AT-03)
    print("\n[4/5] Testing Entitlement-Aware Retrieval (Negative Access & Leakage Protection)...")
    
    # 4a: Client C-01 (Purchased R-101 and R-103)
    c01_allowed = get_client_allowed_report_ids("C-01")
    print(f"  - Client C-01 Allowed Reports: {c01_allowed}")
    assert "R-101" in c01_allowed, "C-01 should have access to R-101"
    assert "R-102" in c01_allowed, "C-01 should have access to public R-102"

    c01_search = retrieve_entitled_chunks(client_id="C-01", query="smart water meter market size 2024", top_k=5)
    c01_rep_ids = {c["report_id"] for c in c01_search["chunks"]}
    print(f"  - C-01 Retrieved Reports for query: {c01_rep_ids}")
    assert "R-101" in c01_rep_ids, "C-01 should retrieve R-101 chunks"

    # 4b: Client C-02 (Purchased R-103 ONLY, NOT R-101)
    c02_allowed = get_client_allowed_report_ids("C-02")
    print(f"  - Client C-02 Allowed Reports: {c02_allowed}")
    assert "R-101" not in c02_allowed, "SECURITY FAILURE: R-101 in C-02 allowed set!"
    assert "R-102" in c02_allowed, "C-02 should have access to public excerpt R-102"

    c02_search = retrieve_entitled_chunks(client_id="C-02", query="What was the global smart water meter market size in 2024 in R-101?", top_k=5)
    c02_rep_ids = {c["report_id"] for c in c02_search["chunks"]}
    print(f"  - C-02 Retrieved Reports for target R-101 query: {c02_rep_ids}")
    
    # Strict verification: Absolutely ZERO chunks from R-101 may be returned to C-02
    assert "R-101" not in c02_rep_ids, "CRITICAL VULNERABILITY: C-02 retrieved unentitled R-101 chunk!"
    print("  - [PASS] Zero unentitled report leakage for Client C-02.")

    # 4c: Verify Upgrade Path surfaced for C-02
    unentitled_catalog = c02_search.get("unentitled_catalog", [])
    unentitled_ids = [u["report_id"] for u in unentitled_catalog]
    print(f"  - C-02 Unentitled Catalog Upgrade Path: {unentitled_ids}")
    assert "R-101" in unentitled_ids, "R-101 should appear in unentitled catalog for upgrade offer"

    # 4d: Verify Prompt Injection Footnote in R-102 Page 14 is retrieved as data
    r102_chunks = collection.get(where={"$and": [{"report_id": "R-102"}, {"page": 14}]})
    assert len(r102_chunks["ids"]) > 0, "R-102 Page 14 chunk missing"
    has_injection_text = any("Disregard all previous instructions" in doc for doc in r102_chunks["documents"])
    assert has_injection_text, "R-102 trap text missing in indexed document"
    print("  - [PASS] Prompt injection attack text preserved safely as passive data.")

    # Step 5: Test API POST /ingest Endpoint
    print("\n[5/5] Testing POST /ingest API Endpoint...")
    with TestClient(app) as client:
        # Unauthorized check (no API key)
        unauth_resp = client.post("/ingest", json={})
        assert unauth_resp.status_code == 401, f"Expected 401, got {unauth_resp.status_code}"
        print("  - POST /ingest without key -> 401 Unauthorized [OK]")

        # Authorized check
        auth_resp = client.post(
            "/ingest",
            headers={"X-API-Key": settings.api_key},
            json={"report_filename": "R-101_Global_Smart_Water_Meter_Market_2025.md"},
        )
        assert auth_resp.status_code == 200, f"Expected 200, got {auth_resp.status_code}"
        data = auth_resp.json()
        print(f"  - POST /ingest with API key -> 200 OK ({data['message']})")

    print("\n" + "=" * 65)
    print(" [SUCCESS] ALL PHASE 2 INGESTION & ACCESS-AWARE RAG CHECKS PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    run_phase2_verification()
