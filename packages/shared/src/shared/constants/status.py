"""Status enumerations for documents and processing pipelines."""

from __future__ import annotations

from enum import Enum


class DocumentStatus(str, Enum):
    """Lifecycle status of a document."""

    PENDING = "pending"
    """Document has been created but not yet uploaded."""

    UPLOADING = "uploading"
    """Document content is being transferred."""

    PROCESSING = "processing"
    """Document is being processed (chunked, embedded, indexed)."""

    READY = "ready"
    """Document is fully processed and available for query."""

    FAILED = "failed"
    """Processing failed; see error details for the cause."""

    DELETED = "deleted"
    """Document has been soft-deleted."""


class ProcessingStatus(str, Enum):
    """Granular processing status for pipeline stages."""

    QUEUED = "queued"
    """Processing job is queued and awaiting a worker."""

    CHUNKING = "chunking"
    """Document is being split into chunks."""

    EMBEDDING = "embedding"
    """Chunks are being embedded into vector representations."""

    INDEXING = "indexing"
    """Embeddings are being indexed for search."""

    COMPLETE = "complete"
    """All processing stages completed successfully."""

    FAILED = "failed"
    """Processing failed at some stage."""
