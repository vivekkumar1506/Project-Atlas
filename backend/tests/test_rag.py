"""Automated tests for Phase 2: Ingest API and Access-Aware Retriever."""
import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import app
from backend.app.rag.retriever import (
    get_client_allowed_report_ids,
    retrieve_entitled_chunks,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_ingest_endpoint_unauthorized(client):
    """POST /ingest without X-API-Key should return 401."""
    response = client.post("/ingest", json={})
    assert response.status_code == 401


def test_ingest_endpoint_authorized(client):
    """POST /ingest with valid X-API-Key should return 200."""
    settings = get_settings()
    response = client.post(
        "/ingest",
        headers={"X-API-Key": settings.api_key},
        json={"report_filename": "R-101_Global_Smart_Water_Meter_Market_2025.md"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["success", "partial_failure"]
    assert "reports_processed" in data


def test_entitlement_filtering_c01_vs_c02():
    """Verify pre-LLM security boundary: C-01 can see R-101, C-02 CANNOT see R-101."""
    # Check allowed IDs
    c01_allowed = get_client_allowed_report_ids("C-01")
    c02_allowed = get_client_allowed_report_ids("C-02")

    assert "R-101" in c01_allowed
    assert "R-101" not in c02_allowed
    assert "R-102" in c01_allowed  # Public excerpt
    assert "R-102" in c02_allowed  # Public excerpt

    # Negative retrieval test for C-02
    c02_result = retrieve_entitled_chunks(
        client_id="C-02",
        query="What is the 2024 global smart water meter market size in R-101?",
        top_k=5,
    )
    retrieved_reports = {c["report_id"] for c in c02_result["chunks"]}

    # STRICT ASSERTION: R-101 chunk must NEVER be returned to C-02
    assert "R-101" not in retrieved_reports
