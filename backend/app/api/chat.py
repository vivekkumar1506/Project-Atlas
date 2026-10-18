"""Chat and Escalation API endpoints for Project Atlas."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.agent.workflow import run_agent_workflow
from backend.app.schemas.contracts import (
    ChatRequest,
    ChatResponse,
    EscalationRecord,
)
from backend.app.security.auth import verify_api_key
from backend.app.services.db import get_db

router = APIRouter(tags=["Chat & Escalations"])
logger = logging.getLogger("atlas.api.chat")


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask Market Research Copilot",
    description="Processes research questions, applies pre-LLM entitlements, detects conflicts, performs deterministic calculations, and formats answers with citations.",
)
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Submit a question to the Report Copilot."""
    logger.info(f"Received chat request from client '{request.client_id}': '{request.question[:60]}...'")
    return run_agent_workflow(request=request, db=db)


@router.get(
    "/escalations",
    response_model=List[EscalationRecord],
    summary="Review Escalation Tickets",
    description="Retrieves open and reviewed escalation tickets for human analysts.",
)
def list_escalations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (open, in_progress, resolved)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> List[EscalationRecord]:
    """List escalation tickets from MySQL."""
    query = "SELECT ticket_id, conversation_id, client_id, question, reason, confidence, status, created_at, assigned_to FROM escalations"
    params = {"limit": limit}

    if status_filter:
        query += " WHERE status = :status"
        params["status"] = status_filter

    query += " ORDER BY created_at DESC LIMIT :limit"

    rows = db.execute(text(query), params).fetchall()

    records = []
    for r in rows:
        records.append(
            EscalationRecord(
                ticket_id=r[0],
                conversation_id=r[1],
                client_id=r[2],
                question=r[3],
                reason=r[4],
                confidence=float(r[5]),
                status=r[6],
                created_at=r[7],
                assigned_to=r[8],
            )
        )
    return records
