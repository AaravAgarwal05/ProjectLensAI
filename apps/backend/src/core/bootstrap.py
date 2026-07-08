"""Application bootstrap — runs once at startup."""

import logging

from fastapi import FastAPI

from src.config.logging import configure_logging
from src.config.settings import get_settings
from src.database.session import init_db

logger = logging.getLogger(__name__)


async def bootstrap_app(app: FastAPI) -> None:
    """Initialize all application services at startup.

    Performs:
        - Logging configuration
        - Database engine initialisation
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

    logger.info("Startup complete — ready to accept requests")
