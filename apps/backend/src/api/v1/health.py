"""Health check endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter

from src.config.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Return service health information.

    Responses:
        200: Service is healthy.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
    }
