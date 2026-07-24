"""Application bootstrap — runs once at startup."""

import logging

from fastapi import FastAPI

from src.ai_core.llm.providers.fallback import FallbackLLMProvider
from src.ai_core.llm.registry import LLMRegistry
from src.config.logging import configure_logging
from src.config.settings import get_settings
from src.database.session import init_db
from src.infra.redis import close_redis, get_redis

logger = logging.getLogger(__name__)


async def bootstrap_app(app: FastAPI) -> None:
    """Initialize all application services at startup.

    Performs:
        - Logging configuration
        - Database engine initialisation
        - LLM provider registration
        - Startup sanity checks

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()
    configure_logging()

    logger.info(
        "Starting %s v%s in %s mode",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.ENV,
    )

    try:
        await init_db(settings.DATABASE_URL)
        logger.info("Database engine initialised successfully")
    except Exception as exc:
        logger.warning("Database initialisation failed: %s. App will run without DB.", exc)

    # ------------------------------------------------------------------
    # Redis client
    # ------------------------------------------------------------------
    try:
        await get_redis()
        logger.info("Redis client initialised successfully")
    except Exception as exc:
        logger.warning("Redis initialisation failed: %s. App will run without Redis.", exc)

    # ------------------------------------------------------------------
    # LLM provider registration
    # ------------------------------------------------------------------
    _registry = LLMRegistry()
    _registry.register("fallback", FallbackLLMProvider)
    logger.info("Registered LLM provider: fallback")
    # Attach to app state for downstream use
    app.state.llm_registry = _registry

    logger.info("Startup complete — ready to accept requests")


async def shutdown_app() -> None:
    """Clean up application resources at shutdown."""
    try:
        await close_redis()
    except Exception as exc:
        logger.warning("Redis shutdown error: %s", exc)
