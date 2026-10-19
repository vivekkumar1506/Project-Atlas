"""Automated Security & Access Control Suite: API Authentication & Client Access.

Tests:
1. Protection on every protected endpoint (POST /chat, GET /escalations, POST /ingest).
2. Rejection of requests with missing X-API-Key (HTTP 401 Unauthorized).
3. Rejection of requests with invalid X-API-Key (HTTP 403 Forbidden).
4. Client identity verification: only registered, active client identities succeed.
5. Unknown or spoofed client identities fail (HTTP 401 Unauthorized).
6. Verification that public monitoring endpoints remain accessible without API keys.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==============================================================================
# 1. POST /chat Authentication & Client Access Tests
# ==============================================================================

def test_chat_endpoint_missing_api_key_unauthorized(client):
    """Direct request to POST /chat with NO X-API-Key must return 401 Unauthorized."""
    response = client.post(
        "/chat",
        json={"client_id": "C-01", "question": "What was the 2024 smart water market size?"},
    )
    assert response.status_code == 401
    assert "Missing required service authentication header" in response.json()["detail"]


def test_chat_endpoint_invalid_api_key_forbidden(client):
    """Direct request to POST /chat with invalid/forged X-API-Key must return 403 Forbidden."""
    response = client.post(
        "/chat",
        headers={"X-API-Key": "malicious_fake_api_key_attempt"},
        json={"client_id": "C-01", "question": "What was the 2024 smart water market size?"},
    )
    assert response.status_code == 403
    assert "Invalid or unauthorized API key" in response.json()["detail"]


def test_chat_endpoint_authorized_valid_client(client):
    """Request with valid X-API-Key and valid client identity C-01 succeeds with 200."""
    settings = get_settings()
    response = client.post(
        "/chat",
        headers={"X-API-Key": settings.api_key},
        json={"client_id": "C-01", "question": "What was the 2024 smart water market size?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["citations"]) >= 1


def test_chat_endpoint_unknown_client_identity_rejected(client):
    """Request with valid X-API-Key but unknown/unregistered client identity (e.g. C-999) must be rejected."""
    settings = get_settings()
    response = client.post(
        "/chat",
        headers={"X-API-Key": settings.api_key},
        json={"client_id": "C-999_UNREGISTERED", "question": "What was the 2024 smart water market size?"},
    )
    assert response.status_code == 401
    assert "not recognized or authenticated" in response.json()["detail"]


# ==============================================================================
# 2. GET /escalations Authentication Tests
# ==============================================================================

def test_escalations_endpoint_missing_api_key_unauthorized(client):
    """Direct request to GET /escalations with NO X-API-Key must return 401 Unauthorized."""
    response = client.get("/escalations")
    assert response.status_code == 401
    assert "Missing required service authentication header" in response.json()["detail"]


def test_escalations_endpoint_invalid_api_key_forbidden(client):
    """Direct request to GET /escalations with invalid X-API-Key must return 403 Forbidden."""
    response = client.get(
        "/escalations",
        headers={"X-API-Key": "unauthorized_key_xyz"},
    )
    assert response.status_code == 403
    assert "Invalid or unauthorized API key" in response.json()["detail"]


def test_escalations_endpoint_authorized_success(client):
    """Request to GET /escalations with valid X-API-Key returns 200 OK."""
    settings = get_settings()
    response = client.get(
        "/escalations",
        headers={"X-API-Key": settings.api_key},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ==============================================================================
# 3. POST /ingest Authentication Tests
# ==============================================================================

def test_ingest_endpoint_missing_api_key_unauthorized(client):
    """Direct request to POST /ingest with NO X-API-Key must return 401 Unauthorized."""
    response = client.post("/ingest", json={})
    assert response.status_code == 401
    assert "Missing required service authentication header" in response.json()["detail"]


def test_ingest_endpoint_invalid_api_key_forbidden(client):
    """Direct request to POST /ingest with invalid X-API-Key must return 403 Forbidden."""
    response = client.post(
        "/ingest",
        headers={"X-API-Key": "fake_admin_token"},
        json={},
    )
    assert response.status_code == 403
    assert "Invalid or unauthorized API key" in response.json()["detail"]


# ==============================================================================
# 4. Public Endpoints Accessibility
# ==============================================================================

def test_public_health_and_root_remain_accessible_without_api_key(client):
    """Monitoring and root endpoints must remain accessible without API keys for container probes."""
    root_res = client.get("/")
    assert root_res.status_code == 200

    health_res = client.get("/health")
    assert health_res.status_code in [200, 503]
