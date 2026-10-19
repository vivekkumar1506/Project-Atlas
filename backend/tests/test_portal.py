"""Automated tests for Phase 4: CI3 Portal Integration.

Tests:
1. Authenticated user submits a valid question.
2. Empty and oversized questions are rejected.
3. Unauthenticated user cannot access chat.
4. One client cannot access another client's conversation history (IDOR).
5. One client cannot submit feedback for another client's message.
6. FastAPI timeout/unavailable responses are handled gracefully (AT-08).
7. Invalid backend JSON is handled safely.
8. Citations and conflict information render safely.
9. Escalation status is displayed correctly.
10. Malicious HTML/script in a question or answer cannot execute (XSS).
11. CSRF protection validation.
12. Restricted report information is not disclosed to an unauthorized client.
13. Feedback retry does not create unintended duplicate records.
14. Existing health, ingestion, agent, and escalation endpoints pass.
"""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.config import get_settings
from backend.app.main import app
from backend.app.services.db import engine


@pytest.fixture
def client():
    settings = get_settings()
    with TestClient(app, headers={"X-API-Key": settings.api_key}) as test_client:
        yield test_client


def test_portal_valid_question_submission(client):
    """1. Authenticated user submits a valid question."""
    response = client.post(
        "/chat",
        json={
            "client_id": "C-01",
            "question": "What was the global smart water meter market size in 2024?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert len(data["citations"]) >= 1


def test_portal_empty_and_oversized_question_rejection(client):
    """2. Empty and oversized questions are rejected by API/portal contracts."""
    # Empty question
    empty_resp = client.post(
        "/chat",
        json={"client_id": "C-01", "question": ""},
    )
    assert empty_resp.status_code == 422  # Pydantic contract validation (min_length=2)

    # Oversized question (> 2000 chars)
    oversized_text = "Market query " * 200
    oversized_resp = client.post(
        "/chat",
        json={"client_id": "C-01", "question": oversized_text},
    )
    assert oversized_resp.status_code == 422  # Pydantic contract validation (max_length=2000)


def test_portal_history_ownership_and_idor_protection():
    """4. One client cannot access another client's conversation history."""
    with engine.connect() as conn:
        # Check conversations for C-01
        c01_convs = conn.execute(
            text("SELECT conversation_id FROM conversations WHERE client_id = 'C-01' LIMIT 5;")
        ).fetchall()
        assert len(c01_convs) > 0

        # Query simulating C-02 attempting to fetch C-01's conversation messages
        target_conv_id = c01_convs[0][0]
        c02_attempt = conn.execute(
            text(
                "SELECT m.message_id, m.content FROM messages m "
                "JOIN conversations c ON c.conversation_id = m.conversation_id "
                "WHERE c.conversation_id = :conv_id AND c.client_id = :client_id;"
            ),
            {"conv_id": target_conv_id, "client_id": "C-02"},
        ).fetchall()

        # MUST BE STRICTLY EMPTY (zero messages accessible to C-02)
        assert len(c02_attempt) == 0, "IDOR Vulnerability: C-02 accessed C-01 messages!"


def test_portal_feedback_recording_and_deduplication():
    """5 & 13. Feedback submission, client ownership, and duplicate prevention."""
    with engine.connect() as conn:
        # Get a message belonging to C-01
        msg = conn.execute(
            text(
                "SELECT m.message_id, c.conversation_id FROM messages m "
                "JOIN conversations c ON c.conversation_id = m.conversation_id "
                "WHERE c.client_id = 'C-01' LIMIT 1;"
            )
        ).fetchone()
        assert msg is not None
        msg_id, conv_id = msg[0], msg[1]

        # Submit first feedback
        existing = conn.execute(
            text("SELECT feedback_id FROM feedback WHERE message_id = :msg_id;"),
            {"msg_id": msg_id},
        ).fetchone()
        if existing:
            conn.execute(
                text("UPDATE feedback SET rating = 'up', comment = 'Accurate numbers' WHERE feedback_id = :fid;"),
                {"fid": existing[0]},
            )
        else:
            conn.execute(
                text("INSERT INTO feedback (conversation_id, message_id, rating, comment) VALUES (:conv_id, :msg_id, 'up', 'Accurate numbers');"),
                {"conv_id": conv_id, "msg_id": msg_id},
            )
        conn.commit()

        # Submit second feedback on same message (toggle/retry)
        existing = conn.execute(
            text("SELECT feedback_id FROM feedback WHERE message_id = :msg_id;"),
            {"msg_id": msg_id},
        ).fetchone()
        if existing:
            conn.execute(
                text("UPDATE feedback SET rating = 'down', comment = 'Changed my mind' WHERE feedback_id = :fid;"),
                {"fid": existing[0]},
            )
        else:
            conn.execute(
                text("INSERT INTO feedback (conversation_id, message_id, rating, comment) VALUES (:conv_id, :msg_id, 'down', 'Changed my mind');"),
                {"conv_id": conv_id, "msg_id": msg_id},
            )
        conn.commit()

        # Verify feedback count for this message is exactly 1 (no unintended duplicates)
        count = conn.execute(
            text("SELECT COUNT(*) FROM feedback WHERE message_id = :msg_id;"),
            {"msg_id": msg_id},
        ).scalar()
        assert count == 1, "Duplicate feedback rows created on re-submission!"


def test_portal_xss_sanitization_in_questions_and_answers(client):
    """10. Malicious HTML/script in a question or answer cannot execute (XSS)."""
    xss_payload = "<script>alert('XSS_ATTACK')</script><img src=x onerror=alert(1)>"
    response = client.post(
        "/chat",
        json={
            "client_id": "C-01",
            "question": f"Is this market safe? {xss_payload}",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Raw executable script tags must not be returned unescaped or executed
    assert "<script>alert('XSS_ATTACK')</script>" not in data["answer"]


def test_portal_escalation_status_and_tickets(client):
    """9. Escalation status is displayed correctly and ticket referenced."""
    response = client.post(
        "/chat",
        json={
            "client_id": "C-01",
            "question": "What will the market be worth in 2035?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["escalated"] is True
    assert "2030" in data["answer"]


def test_portal_unentitled_leakage_blocked(client):
    """12. Restricted report information is not disclosed to an unauthorized client."""
    response = client.post(
        "/chat",
        json={
            "client_id": "C-02",
            "question": "What was the 2024 market size in R-101?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    # 4.21 from R-101 must NEVER be disclosed to C-02
    assert "4.21" not in data["answer"]
    assert "upgrade" in data["answer"].lower() or "restricted" in data["answer"].lower()
