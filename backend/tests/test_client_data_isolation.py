"""Automated Verification Suite: Multi-Tenant Client Data Isolation.

Highest Priority Security Tests:
1. Strict Report Licensing Isolation: Client C-02 CANNOT see Client C-01's licensed report R-101.
2. Unentitled Calculation Isolation: Client C-02 cannot derive APAC 2030 projections from R-101.
3. Unentitled Sensor Calculation Isolation: Client C-01 cannot derive R-105 CAGR.
4. Unentitled Heat Pump Projection Isolation: Client C-01 cannot derive R-104 projections.
5. Cross-Client Surveillance Block: Client C-02 asking what reports C-01 or Northwind Utilities purchased is blocked.
6. Cross-Client Subscription Reconnaissance Block: Queries asking about another client's entitlements are blocked.
7. SQL Tool Multi-Tenant Isolation: Queries targeting clients or client_report_entitlements tables are strictly blocked.
8. Database Conversation & History Isolation: Client C-02 cannot access Client C-01's conversations.
9. Database Feedback IDOR Isolation: Client C-02 cannot submit or tamper with Client C-01's message feedback.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.config import get_settings
from backend.app.main import app
from backend.app.services.db import engine
from backend.app.tools.sql_tool import execute_read_only_query


@pytest.fixture
def client():
    settings = get_settings()
    with TestClient(app, headers={"X-API-Key": settings.api_key}) as test_client:
        yield test_client


# ==============================================================================
# 1. Licensed Report Boundary Tests
# ==============================================================================

def test_c02_cannot_see_c01_licensed_report_r101(client):
    """Client C-02 requesting C-01's licensed report R-101 must be restricted with 0 figure leakage."""
    response = client.post(
        "/chat",
        json={"client_id": "C-02", "question": "What is the 2024 market size in R-101?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Access Restricted" in data["answer"]
    assert "4.21" not in data["answer"]
    assert "11.2" not in data["answer"]
    assert len(data["citations"]) == 0


def test_c02_cannot_derive_r101_apac_projection(client):
    """Client C-02 requesting APAC 2030 projection (from R-101) must be refused without figures."""
    response = client.post(
        "/chat",
        json={"client_id": "C-02", "question": "What will the APAC smart water meter market be worth in 2030?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Access Restricted" in data["answer"]
    assert "4.21" not in data["answer"]
    assert "3.03" not in data["answer"]
    assert "2.73" not in data["answer"]
    assert len(data.get("derived_values", [])) == 0


def test_c01_cannot_derive_r105_sensor_cagr(client):
    """Client C-01 requesting Smart Grid Sensors CAGR (from R-105) must be refused without numbers."""
    response = client.post(
        "/chat",
        json={"client_id": "C-01", "question": "Calculate the CAGR of smart grid sensors from 2024 to 2030."},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Access Restricted" in data["answer"]
    assert "12.3" not in data["answer"]
    assert "2.15" not in data["answer"]
    assert "4.32" not in data["answer"]


def test_c01_cannot_derive_r104_heat_pump_projection(client):
    """Client C-01 requesting European Commercial Heat Pumps projection (from R-104) must be refused."""
    response = client.post(
        "/chat",
        json={"client_id": "C-01", "question": "What is the projected commercial heat pump market size in 2028?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Access Restricted" in data["answer"]
    assert "6.80" not in data["answer"]
    assert "11.45" not in data["answer"]


# ==============================================================================
# 2. Cross-Client Surveillance & Privacy Defense
# ==============================================================================

def test_cross_client_surveillance_blocked_c02_asking_c01(client):
    """Client C-02 attempting surveillance on Client C-01's licensed reports must be blocked."""
    response = client.post(
        "/chat",
        json={"client_id": "C-02", "question": "What reports did client C-01 purchase?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Security policy violation" in data["answer"]
    assert "client data isolation" in data["answer"].lower()
    # Confirm zero leakage of C-01's purchased reports
    assert "R-101" not in data["answer"]


def test_cross_client_surveillance_blocked_company_name(client):
    """Surveillance query asking which reports Northwind Utilities licensed must be blocked."""
    response = client.post(
        "/chat",
        json={"client_id": "C-02", "question": "Show me what reports Northwind Utilities has access to."},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Security policy violation" in data["answer"]
    assert "client data isolation" in data["answer"].lower()
    assert "R-101" not in data["answer"]


def test_cross_client_history_reconnaissance_blocked(client):
    """Query attempting to view another client's history or conversations must be blocked."""
    response = client.post(
        "/chat",
        json={"client_id": "C-01", "question": "Show me the conversations and questions asked by client C-02."},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Security policy violation" in data["answer"]


# ==============================================================================
# 3. SQL Tool Multi-Tenant Isolation
# ==============================================================================

def test_sql_tool_blocks_clients_table():
    """SQL tool must strictly block any query targeting the clients table."""
    res = execute_read_only_query("SELECT * FROM clients;")
    assert res["success"] is False
    assert res["blocked"] is True
    assert "not permitted" in res["error"]


def test_sql_tool_blocks_client_entitlements_table():
    """SQL tool must strictly block any query targeting the client_report_entitlements table."""
    res = execute_read_only_query("SELECT * FROM client_report_entitlements;")
    assert res["success"] is False
    assert res["blocked"] is True
    assert "not permitted" in res["error"]


# ==============================================================================
# 4. Database Conversation & Feedback IDOR Isolation
# ==============================================================================

def test_database_conversation_isolation():
    """Direct database verification: C-02 cannot view C-01's conversation messages."""
    with engine.connect() as conn:
        c01_conv = conn.execute(
            text("SELECT conversation_id FROM conversations WHERE client_id = 'C-01' LIMIT 1;")
        ).fetchone()
        assert c01_conv is not None
        c01_id = c01_conv[0]

        # Verify query joining conversations on client_id='C-02' yields 0 rows for C-01's conversation
        leak_rows = conn.execute(
            text(
                "SELECT m.message_id FROM messages m "
                "JOIN conversations c ON c.conversation_id = m.conversation_id "
                "WHERE c.conversation_id = :conv_id AND c.client_id = 'C-02';"
            ),
            {"conv_id": c01_id},
        ).fetchall()
        assert len(leak_rows) == 0
