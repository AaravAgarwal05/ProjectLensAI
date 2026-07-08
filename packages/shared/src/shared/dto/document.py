"""Data transfer objects for document filtering and sorting."""

from __future__ import annotations

from datetime import datetime

from pydantic.main import BaseModel


class DocumentFilterDTO(BaseModel):
    """DTO carrying document query filter criteria.

    All fields are optional; filters are applied only for non-``None`` values.

    Attributes:
        status: Filter by document processing status.
        date_from: Lower bound for document creation date.
        date_to: Upper bound for document creation date.
        search: Full-text search term.
    """

    status: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = None


class DocumentSortDTO(BaseModel):
    """DTO carrying document sort parameters.

    Attributes:
        field: Field name to sort by (defaults to ``"created_at"``).
        direction: Sort direction, ``"asc"`` or ``"desc"`` (defaults to ``"desc"``).
    """

    field: str = "created_at"
    direction: str = "desc"
