"""Vector-store models for the indexing engine.

A ``VectorDocument`` is the unit of persistence — a stored embedded chunk
with optional metadata that supports filtering.

Output models (``IndexingResult``, ``DeleteResult``, ``UpdateResult``)
are returned by the indexing engine after batch operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VectorMetadata(BaseModel):
    """Metadata attached to every stored vector.

    Attributes:
        chunk_id: UUID linking back to the source ``Chunk``.
        report_id: Document report identifier.
        version_id: Document version identifier (optional).
        embedding_model: Model that produced this vector.
        embedding_provider: Provider that produced this vector.
        created_at: When the vector was embedded.
        extra: Provider-specific metadata.
    """

    chunk_id: str = ""
    report_id: str = ""
    version_id: str = ""
    embedding_model: str = ""
    embedding_provider: str = ""
    created_at: datetime | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class VectorDocument(BaseModel):
    """A single vector document stored in the index.

    Attributes:
        id: Unique identifier within the collection.
        chunk_id: Link back to the source ``Chunk``.
        vector: The embedding vector as a list of floats.
        metadata: Structured :class:`VectorMetadata`.
    """

    id: str = ""
    chunk_id: str
    vector: list[float]
    dimensions: int = 0
    metadata: VectorMetadata = Field(default_factory=VectorMetadata)


class IndexingStatistics(BaseModel):
    """Aggregate statistics for an indexing operation.

    Attributes:
        total_documents: Number of documents processed.
        successful: Number of successfully indexed documents.
        failed: Number of documents that failed to index.
        total_time: Wall-clock time in seconds.
        throughput: Documents per second.
        avg_latency: Average latency per batch.
        memory_usage: Approximate memory delta (bytes).
    """

    total_documents: int = 0
    successful: int = 0
    failed: int = 0
    total_time: float = 0.0
    throughput: float = 0.0
    avg_latency: float = 0.0
    memory_usage: int | None = None


class IndexingResult(BaseModel):
    """Result of an indexing pipeline run.

    Attributes:
        documents: The indexed ``VectorDocument`` objects.
        statistics: Aggregate :class:`IndexingStatistics`.
        collection_name: Target collection name.
        warnings: Non-fatal warnings.
        errors: Fatal errors.
        successful: Whether the run completed without fatal error.
    """

    documents: list[VectorDocument] = Field(default_factory=list)
    statistics: IndexingStatistics = Field(default_factory=IndexingStatistics)
    collection_name: str = ""
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    successful: bool = True


class DeleteResult(BaseModel):
    """Result of a delete operation.

    Attributes:
        deleted_count: Number of deleted documents.
        collection_name: Target collection name.
        warnings: Non-fatal warnings.
        errors: Fatal errors.
        successful: Whether the operation completed without fatal error.
    """

    deleted_count: int = 0
    collection_name: str = ""
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    successful: bool = True


class UpdateResult(BaseModel):
    """Result of an update operation.

    Attributes:
        updated_count: Number of updated documents.
        collection_name: Target collection name.
        warnings: Non-fatal warnings.
        errors: Fatal errors.
        successful: Whether the operation completed without fatal error.
    """

    updated_count: int = 0
    collection_name: str = ""
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    successful: bool = True
