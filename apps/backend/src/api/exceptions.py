"""Exception handlers that return consistent JSON error responses."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

logger = logging.getLogger(__name__)


class ProjectLensError(Exception):
    """Base application-level exception with structured context."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "internal_error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


def _error_response(
    message: str,
    code: str = "error",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Format standard HTTP exceptions as JSON."""
    return _error_response(
        message=exc.detail,
        code="http_error",
        status_code=exc.status_code,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Format pydantic / request validation errors."""
    return _error_response(
        message="Request validation failed",
        code="validation_error",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": exc.errors()},
    )


async def project_lens_error_handler(
    request: Request,
    exc: ProjectLensError,
) -> JSONResponse:
    """Format application-level errors."""
    return _error_response(
        message=exc.message,
        code=exc.code,
        status_code=exc.status_code,
        details=exc.details,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions — logs the traceback."""
    logger.exception("Unhandled exception: %s", exc)
    return _error_response(
        message="An internal server error occurred",
        code="internal_error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ProjectLensError, project_lens_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
