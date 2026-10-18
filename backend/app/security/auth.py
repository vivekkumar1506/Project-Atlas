import secrets
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.app.config import get_settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
settings = get_settings()


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify service-to-service API key for protected routes."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required service authentication header: X-API-Key",
        )
    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or unauthorized API key",
        )
    return api_key
