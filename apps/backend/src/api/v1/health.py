"""Health check endpoint with full dependency checks."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter
from sqlalchemy import text

from src.api.rate_limiter import limiter
from src.config.settings import get_settings
from src.database import session as db_session
from src.infra.redis import health_check_redis

logger = logging.getLogger(__name__)

router = APIRouter()

# Server start wall-clock — used to report uptime in /health.
_START = time.monotonic()


async def _check_database() -> dict[str, Any]:
    """Check database connectivity with a SELECT 1."""
    try:
        factory = db_session.async_session_factory
        if factory is None:
            return {"status": "error", "latency_ms": 0}
        async with factory() as session:
            start = time.monotonic()
            await session.execute(text("SELECT 1"))
            latency_ms = int((time.monotonic() - start) * 1000)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return {"status": "error", "latency_ms": 0}


async def _check_vector_store() -> dict[str, Any]:
    """Check vector-store connectivity via health_check."""
    try:
        from src.ai_core.vector_store.factory import build_vector_store

        settings = get_settings()
        store = build_vector_store(settings)
        start = time.monotonic()
        ok = await store.health_check()
        latency_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "ok" if ok else "error",
            "latency_ms": latency_ms,
            "provider": store.store_name,
        }
    except Exception as exc:
        logger.warning("Vector store health check failed: %s", exc)
        return {"status": "error", "latency_ms": 0, "provider": ""}


async def _check_ollama() -> dict[str, Any]:
    """Check Ollama connectivity by fetching model tags."""
    try:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=5) as client:
            start = time.monotonic()
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.status_code == 200:
                return {"status": "ok", "latency_ms": latency_ms}
            return {"status": "error", "latency_ms": latency_ms}
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return {"status": "error", "latency_ms": 0}


async def _check_redis() -> dict[str, Any]:
    """Check Redis connectivity."""
    return await health_check_redis()


@router.get("/health")
@limiter.exempt
async def health_check() -> dict[str, Any]:
    """Return comprehensive service health information.

    Checks database, vector store, Ollama, and Redis connectivity,
    then aggregates the results into an overall status.

    Responses:
        200: Service health information with per-dependency status.
    """
    settings = get_settings()

    db_result = await _check_database()
    vector_result = await _check_vector_store()
    ollama_result = await _check_ollama()
    redis_result = await _check_redis()

    checks = {
        "database": db_result,
        "vector_store": vector_result,
        "ollama": ollama_result,
        "redis": redis_result,
    }

    # Determine overall status
    if db_result["status"] == "error":
        overall = "down"
    elif any(c["status"] == "error" for c in checks.values()):
        overall = "degraded"
    else:
        overall = "ok"

    return {
        "status": overall,
        "version": settings.VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime_seconds": int(time.monotonic() - _START),
        "checks": checks,
    }
