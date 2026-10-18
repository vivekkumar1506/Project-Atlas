"""Ingestion API endpoints."""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.rag.ingestion import ingest_all_reports, ingest_report
from backend.app.security.auth import verify_api_key

router = APIRouter(tags=["Ingestion"])
logger = logging.getLogger("atlas.api.ingest")


class IngestReportRequest(BaseModel):
    report_filename: Optional[str] = Field(
        None,
        description="Specific report filename to ingest",
        json_schema_extra={"example": "R-101_Global_Smart_Water_Meter_Market_2025.md"},
    )


class IngestResponse(BaseModel):
    status: str
    message: str
    reports_processed: int
    details: List[Dict[str, Any]]


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest Market Reports",
    description="Parses report documents, extracts page metadata, builds embeddings, and stores chunks in the Vector DB.",
)
def trigger_ingest(
    payload: Optional[IngestReportRequest] = None,
    api_key: str = Depends(verify_api_key),
) -> IngestResponse:
    """Trigger ingestion of reports into ChromaDB with metadata."""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    reports_dir = base_dir / "reports"

    if not reports_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reports directory not found at {reports_dir}",
        )

    if payload and payload.report_filename:
        target_file = reports_dir / payload.report_filename
        if not target_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report file {payload.report_filename} not found",
            )
        result = ingest_report(target_file)
        return IngestResponse(
            status="success" if result["status"] == "success" else "partial_failure",
            message=f"Single report {payload.report_filename} processed",
            reports_processed=1,
            details=[result],
        )

    # Ingest all reports in directory
    results = ingest_all_reports(reports_dir)
    success_count = sum(1 for r in results if r.get("status") == "success")

    return IngestResponse(
        status="success" if success_count == len(results) else "partial_failure",
        message=f"Ingested {success_count} of {len(results)} reports successfully",
        reports_processed=len(results),
        details=results,
    )
