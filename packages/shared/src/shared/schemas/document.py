"""API schemas for document create, update, and response operations."""

from __future__ import annotations

from pydantic import Field
from pydantic.main import BaseModel

from shared.models.document import Document, DocumentMetadata


class DocumentCreate(BaseModel):
    """Request schema for uploading a new document.

    Attributes:
        filename: Original file name.
        content_type: MIME type of the document.
        size: File size in bytes.
        metadata: Optional document metadata.
    """

    filename: str
    content_type: str
    size: int
    metadata: DocumentMetadata | None = None


class DocumentUpdate(BaseModel):
    """Request schema for updating an existing document's metadata.

    All fields are optional; only provided fields are applied.
    """

    filename: str | None = None
    metadata: DocumentMetadata | None = None
    status: str | None = None


class DocumentResponse(Document):
    """Response schema for a document, extending the domain model with client state.

    Attributes:
        is_favorite: Whether the current user has favourited this document.
    """

    is_favorite: bool = False
