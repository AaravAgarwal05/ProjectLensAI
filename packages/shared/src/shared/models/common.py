"""Pydantic models shared across the platform (generic wrappers, pagination, errors)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import Field
from pydantic.main import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """A generic paginated response envelope.

    Attributes:
        items: List of items for the current page.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        has_more: Whether additional pages exist.
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool = False


class APIResponse(BaseModel, Generic[T]):
    """A generic API response envelope.

    Attributes:
        success: Whether the request succeeded.
        data: Optional response payload.
        error: Optional error message on failure.
        timestamp: Response timestamp (defaults to UTC now).
    """

    success: bool
    data: T | None = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorResponse(BaseModel):
    """A structured error representation.

    Attributes:
        code: Machine-readable error code (e.g. ``"NOT_FOUND"``).
        message: Human-readable error description.
        details: Optional dictionary of additional error context.
    """

    code: str
    message: str
    details: dict | None = None
