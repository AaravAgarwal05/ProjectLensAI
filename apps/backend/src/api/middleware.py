"""Custom middleware registration for the FastAPI application."""

import logging
import time

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Adds an X-Process-Time header with the request duration in seconds."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response


def add_middleware(app: FastAPI) -> None:
    """Register all custom middleware on the application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_middleware(TimingMiddleware)
    logger.debug("Custom middleware registered")
