"""Chunk models for the chunking engine.

Every chunker produces ``Chunk`` objects.  A chunk is a self-contained
text fragment with rich metadata about its provenance in the source
document.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attached to every chunk.

    Attributes:
        page_number: 1-indexed page the chunk originates from (if known).
        section: Section or chapter heading the chunk falls under.
        heading: The nearest (sub)heading above this chunk.
        parent_chunk_id: UUID of the parent chunk (for hierarchical chunking).
        source: Identifier of the chunker that produced this chunk.
        document_title: Title inherited from the parsed document.
        document_author: Author inherited from the parsed document.
        language: Language code inherited from the parsed document.
        extra: Arbitrary additional metadata.
    """

    page_number: int | None = None
    section: str | None = None
    heading: str | None = None
    parent_chunk_id: str | None = None
    source: str = "unknown"
    document_title: str | None = None
    document_author: str | None = None
    language: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    """A single chunk produced by a chunking strategy.

    Attributes:
        chunk_id: Unique identifier for this chunk.
        report_id: Identifier linking back to the source report.
        report_version_id: Identifier linking back to the report version.
        chunk_index: Zero-based index of this chunk in the sequence.
        page_number: 1-indexed page this chunk was extracted from.
        start_offset: Character offset (inclusive) in the cleaned document text.
        end_offset: Character offset (exclusive) in the cleaned document text.
        text: The chunk text content.
        token_count: Approximate token count (4 chars per token heuristic).
        section: Section heading this chunk belongs to.
        heading: Nearest heading above this chunk.
        parent_chunk_id: UUID of the parent chunk (hierarchical chunking).
        metadata: Structured :class:`ChunkMetadata`.
        created_at: Timestamp when this chunk was created.
    """

    model_config = {"frozen": True}

    chunk_id: str = Field(default_factory=lambda: str(uuid4()))
    report_id: str | None = None
    report_version_id: str | None = None
    chunk_index: int = 0
    page_number: int | None = None
    start_offset: int = 0
    end_offset: int = 0
    text: str
    token_count: int = 0
    section: str | None = None
    heading: str | None = None
    parent_chunk_id: str | None = None
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChunkStatistics(BaseModel):
    """Aggregate statistics for a chunking run.

    Attributes:
        number_of_chunks: Total chunk count.
        average_chunk_size: Mean character length of chunks.
        average_tokens_per_chunk: Mean token count per chunk.
        largest_chunk: Maximum character length.
        smallest_chunk: Minimum character length.
        processing_time: Wall-clock time for the chunking run (seconds).
        memory_usage: Approximate memory used in bytes (optional).
        source: Chunker name that produced these stats.
        chunk_size_std_dev: Standard deviation of chunk sizes.
    """

    number_of_chunks: int = 0
    average_chunk_size: float = 0
    average_tokens_per_chunk: float = 0
    largest_chunk: int = 0
    smallest_chunk: int = 0
    processing_time: float = 0.0
    memory_usage: int | None = None
    source: str = "unknown"
    chunk_size_std_dev: float = 0.0


class ChunkingResult(BaseModel):
    """The complete output of a chunking pipeline run.

    Attributes:
        chunks: The produced chunks.
        statistics: Aggregate :class:`ChunkStatistics`.
        warnings: Non-fatal warnings generated during chunking.
        errors: Fatal errors (if any) during chunking.
        successful: Whether chunking completed without fatal error.
    """

    chunks: list[Chunk] = Field(default_factory=list)
    statistics: ChunkStatistics = Field(default_factory=ChunkStatistics)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    successful: bool = True
