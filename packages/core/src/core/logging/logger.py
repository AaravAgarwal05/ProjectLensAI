"""Logging utilities."""

import json
import logging
import sys
from typing import Any

from core.logging.config import LoggingConfig


class JsonFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra
        return json.dumps(log_entry)


_LOGGER_CACHE: dict[str, logging.Logger] = {}
_DEFAULT_CONFIG = LoggingConfig()


def get_logger(name: str, config: LoggingConfig | None = None) -> logging.Logger:
    """Get a structured logger with the given *name*.

    Args:
        name: Logger name (typically ``__name__``).
        config: Optional logging configuration; uses defaults if omitted.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    cfg = config or _DEFAULT_CONFIG
    logger = logging.getLogger(name)
    logger.setLevel(cfg.level.upper())
    logger.handlers.clear()

    if cfg.output == "json":
        fmt: logging.Formatter = JsonFormatter()
    else:
        fmt = logging.Formatter(cfg.format)

    handler: logging.Handler
    if cfg.file_path:
        handler = logging.FileHandler(cfg.file_path)
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.propagate = False

    _LOGGER_CACHE[name] = logger
    return logger


class LoggerMixin:
    """Mixin that provides a ``self.logger`` property.

    Usage::

        class MyClass(LoggerMixin):
            def do_something(self) -> None:
                self.logger.info("doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        """Return a logger named after the class's module."""
        return get_logger(self.__class__.__module__)
