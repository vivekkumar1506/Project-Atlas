from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# Health Check Contracts
# ------------------------------------------------------------------------------

class DatabaseHealth(BaseModel):
    connected: bool = Field(..., description="Whether database is connected")
    database: str = Field(..., description="Target database name")
    latency_ms: Optional[float] = Field(None, description="Connection latency in milliseconds")
    error: Optional[str] = Field(None, description="Sanitized error description if unhealthy")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"}, description="Overall service status")
    service: str = Field(..., json_schema_extra={"example": "Project Atlas AI API"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    database: DatabaseHealth


# ------------------------------------------------------------------------------
# Chat API Contracts (PRD Section 7.1 & 7.2)
# ------------------------------------------------------------------------------

class ChatRequest(BaseModel):
    client_id: str = Field(..., description="Authenticated client identifier", json_schema_extra={"example": "C-01"})
    question: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="Market research question",
        json_schema_extra={"example": "Compare the 2024 market estimates and explain the difference."},
    )
    user_reference: Optional[str] = Field(None, description="Optional portal session or user ID")


class Citation(BaseModel):
    report_id: str = Field(..., json_schema_extra={"example": "R-101"})
    report_title: Optional[str] = Field(None, json_schema_extra={"example": "Global Enterprise Tech Spending 2024"})
    source_location: Optional[str] = Field(None, json_schema_extra={"example": "Page 14, Table 3.2"})
    excerpt: Optional[str] = Field(None, description="Non-restricted public or entitled excerpt")


class Conflict(BaseModel):
    metric_name: str = Field(..., json_schema_extra={"example": "2024 Enterprise Hardware Market"})
    first_report: str = Field(..., json_schema_extra={"example": "R-101"})
    first_value: str = Field(..., json_schema_extra={"example": "$4.21B (includes hardware+software+services)"})
    second_report: str = Field(..., json_schema_extra={"example": "R-102"})
    second_value: str = Field(..., json_schema_extra={"example": "$3.87B (hardware only)"})
    explanation: str = Field(
        ...,
        json_schema_extra={"example": "Scope discrepancy: R-101 includes bundled services whereas R-102 is pure hardware."},
    )


class DerivedValue(BaseModel):
    metric_name: str = Field(..., json_schema_extra={"example": "2024-2030 CAGR"})
    formula: str = Field(
        ...,
        json_schema_extra={"example": "CAGR = (Ending Value / Beginning Value)^(1 / Number of Years) - 1"},
    )
    inputs: Dict[str, Any] = Field(
        ...,
        json_schema_extra={"example": {"beginning_value": 4.21, "ending_value": 7.85, "years": 6}},
    )
    assumptions: List[str] = Field(
        default_factory=list,
        json_schema_extra={"example": ["Base year is 2024", "Constant currency USD"]},
    )
    result: str = Field(..., json_schema_extra={"example": "10.94%"})


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Synthesized answer with citations")
    citations: List[Citation] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0, json_schema_extra={"example": 0.92})
    conflicts: List[Conflict] = Field(default_factory=list)
    derived_values: List[DerivedValue] = Field(default_factory=list)
    escalated: bool = Field(default=False)
    escalation_reason: Optional[str] = None


# ------------------------------------------------------------------------------
# Escalation Contracts (PRD Section 4.7 & 7)
# ------------------------------------------------------------------------------

class EscalationRecord(BaseModel):
    ticket_id: str
    conversation_id: Optional[str] = None
    client_id: str
    question: str
    reason: str
    confidence: float
    status: str
    created_at: datetime
    assigned_to: Optional[str] = None
    supporting_references: Optional[Dict[str, Any]] = None
