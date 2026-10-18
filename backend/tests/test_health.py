import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import get_settings


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test the root '/' endpoint returns 200 with service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["status"] == "online"


def test_health_endpoint(client):
    """Test GET /health returns typed response and database status."""
    response = client.get("/health")
    # Health returns 200 (healthy) or 503 (if degraded without db)
    assert response.status_code in [200, 503]
    data = response.json()

    # Verify response structure according to PRD contracts
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data
    assert "database" in data

    db_info = data["database"]
    assert "connected" in db_info
    assert "database" in db_info
    assert isinstance(db_info["connected"], bool)

    # Crucial security check: Ensure no database passwords leaked in output
    settings = get_settings()
    if settings.mysql_password:
        assert settings.mysql_password not in response.text


def test_health_v1_alias(client):
    """Test /api/v1/health alias endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database" in data
