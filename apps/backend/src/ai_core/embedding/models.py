"""Embedding models for the embedding engine.

An ``EmbeddedChunk`` is the output of the embedding pipeline.
It pairs a ``chunk_id`` with its vector representation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class EmbeddingVector(BaseModel):
    """A single embedding vector.

    Attributes:
        vector: The embedding values as a list of floats.
        dimensions: Dimensionality of the vector.
    """

    vector: list[float]
    dimensions: int

    @classmethod
    def from_list(cls, values: list[float]) -> EmbeddingVector:
        """Create from a list of floats, auto-detecting dimensions."""
        return cls(vector=values, dimensions=len(values))


class EmbeddingMetadata(BaseModel):
    """Metadata attached to every embedded chunk.

    Attributes:
        provider: Name of the embedding provider.
        model: Name of the embedding model.
        batch_index: Index within the batch (if batched).
        chunk_text_length: Character length of the source chunk text.
    """

    provider: str = "unknown"
    model: str = "unknown"
    batch_index: int | None = None
    chunk_text_length: int = 0
    extra: dict[str, Any] = Field(default_factory=dict)


class EmbeddedChunk(BaseModel):
    """A chunk with its embedding vector.

    Attributes:
        chunk_id: UUID linking back to the source ``Chunk``.
        vector: The embedding vector.
        embedding_model: Name of the model that produced this embedding.
        embedding_provider: Name of the provider that produced this embedding.
        dimensions: Dimensionality of the vector.
        created_at: Timestamp when the embedding was created.
        metadata: Structured :class:`EmbeddingMetadata`.
    """

    chunk_id: str
    vector: EmbeddingVector
    embedding_model: str
    embedding_provider: str
    dimensions: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: EmbeddingMetadata = Field(default_factory=EmbeddingMetadata)


class EmbeddingStatistics(BaseModel):
    """Aggregate statistics for an embedding run.

    Attributes:
        total_chunks: Number of chunks embedded.
        total_batches: Number of batches processed.
        average_batch_size: Mean batch size.
        total_processing_time: Total wall-clock time in seconds.
        embedding_latency: Average time per batch in seconds.
        throughput: Chunks per second.
        dimensions: Embedding dimensionality.
        model_name: Model used.
        provider_name: Provider used.
        memory_usage: Approximate memory delta (bytes).
    """

    total_chunks: int = 0
    total_batches: int = 0
    average_batch_size: float = 0.0
    total_processing_time: float = 0.0
    embedding_latency: float = 0.0
    throughput: float = 0.0
    dimensions: int = 0
    model_name: str = ""
    provider_name: str = ""
    memory_usage: int | None = None


class EmbeddingResult(BaseModel):
    """The complete output of an embedding pipeline run.

    Attributes:
        embeddings: The produced ``EmbeddedChunk`` objects.
        statistics: Aggregate :class:`EmbeddingStatistics`.
        warnings: Non-fatal warnings.
        errors: Fatal errors.
        successful: Whether the run completed without fatal error.
    """

    embeddings: list[EmbeddedChunk] = Field(default_factory=list)
    statistics: EmbeddingStatistics = Field(default_factory=EmbeddingStatistics)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    successful: bool = True
