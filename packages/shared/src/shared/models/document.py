"""Pydantic models for document and document-chunk entities."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field
from pydantic.main import BaseModel


class DocumentMetadata(BaseModel):
    """Metadata associated with a document.

    Attributes:
        title: Optional human-readable document title.
        author: Optional document author name.
        page_count: Optional number of pages.
        language: ISO language code (defaults to ``"en"``).
        custom: Arbitrary custom metadata key-value pairs.
    """

    title: str | None = None
    author: str | None = None
    page_count: int | None = None
    language: str = "en"
    custom: dict = Field(default_factory=dict)


class Document(BaseModel):
    """A document uploaded to the platform.

    Attributes:
        id: Unique document identifier.
        filename: Original file name.
        content_type: MIME type of the document.
        size: File size in bytes.
        metadata: Associated :class:`DocumentMetadata`.
        status: Processing status (defaults to ``"pending"``).
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    filename: str
    content_type: str
    size: int
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    status: str = "pending"
    created_at: datetime
    updated_at: datetime


class DocumentChunk(BaseModel):
    """A chunk (segment) of a document used for embedding and retrieval.

    Attributes:
        id: Unique chunk identifier.
        document_id: Identifier of the parent document.
        index: Zero-based position within the document.
        content: Text content of the chunk.
        metadata: Optional metadata key-value pairs.
        embedding: Optional vector embedding representation.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    index: int
    content: str
    metadata: dict = Field(default_factory=dict)
    embedding: list[float] | None = None
