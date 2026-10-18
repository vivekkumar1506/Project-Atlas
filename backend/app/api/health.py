from datetime import datetime, timezone
from fastapi import APIRouter, Response, status

from backend.app.config import get_settings
from backend.app.schemas.contracts import DatabaseHealth, HealthCheckResponse
from backend.app.services.db import check_db_connection

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Service Health Check",
    description="Returns the operational status of the service and database connectivity without exposing sensitive credentials.",
)
def get_health(response: Response) -> HealthCheckResponse:
    """Perform health checks on critical dependencies (MySQL database)."""
    db_status = check_db_connection()

    is_healthy = db_status.get("connected", False)
    service_status = "healthy" if is_healthy else "degraded"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthCheckResponse(
        status=service_status,
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
        database=DatabaseHealth(
            connected=db_status.get("connected", False),
            database=db_status.get("database", settings.mysql_database),
            latency_ms=db_status.get("latency_ms"),
            error=db_status.get("error"),
        ),
    )
