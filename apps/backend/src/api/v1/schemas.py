"""Pydantic request/response models for report management endpoints.

All response models use ``from_attributes=True`` so they can be constructed
directly from SQLAlchemy ORM instances via ``model_validate()``.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


class VersionResponse(BaseModel):
    """Response schema for a single report file version."""

    id: UUID
    version_number: int
    original_filename: str
    mime_type: str
    file_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


class ReportResponse(BaseModel):
    """Response schema for a single report including its version history."""

    id: UUID
    title: str
    description: str | None = None
    department: str | None = None
    author: str | None = None
    tags: list[str] | None = None
    visibility: str
    year: int | None = None
    status: str
    original_filename: str | None = None
    mime_type: str | None = None
    checksum: str | None = None
    file_size: int | None = None
    versions: list[VersionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateReportRequest(BaseModel):
    """Request body for partial report update (PATCH).

    Only fields explicitly present in the JSON payload are applied.
    """

    title: str | None = None
    description: str | None = None
    department: str | None = None
    author: str | None = None
    tags: list[str] | None = None
    visibility: str | None = None
    year: int | None = None
    status: str | None = None


class ReportListResponse(BaseModel):
    """Paginated list of reports."""

    items: list[ReportResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------


class CollectionResponse(BaseModel):
    """Response schema for a single collection."""

    id: UUID
    name: str
    description: str | None = None
    report_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateCollectionRequest(BaseModel):
    """Request body for creating a collection."""

    name: str
    description: str | None = None


class UpdateCollectionRequest(BaseModel):
    """Request body for partial collection update (PATCH)."""

    name: str | None = None
    description: str | None = None


class CollectionListResponse(BaseModel):
    """Paginated list of collections."""

    items: list[CollectionResponse]
    total: int
    skip: int
    limit: int
