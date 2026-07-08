"""Structured logging configuration for the application."""

import logging
import sys

from src.config.settings import get_settings


def configure_logging(level: str | None = None) -> None:
    """Configure structured logging with a console handler.

    Args:
        level: Override log level. Falls back to LOG_LEVEL from settings.
    """
    settings = get_settings()
    log_level = (level or settings.LOG_LEVEL).upper()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Configure uvicorn loggers to use same format
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.addHandler(handler)
        uvicorn_logger.setLevel(log_level)

    # Quiet noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.debug("Logging configured at %s level", log_level)
