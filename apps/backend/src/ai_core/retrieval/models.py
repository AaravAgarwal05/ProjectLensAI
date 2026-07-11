"""Retrieval models — query, chunk, result, metadata, statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SearchQuery:
    """A query to the retrieval pipeline.

    Attributes:
        text: The natural-language query string.
        top_k: Maximum number of chunks to return.
        score_threshold: Minimum similarity score (0..1, optional).
        include_metadata: Whether to include document metadata.
        filter: Metadata filter dict passed to the vector store.
        collection: Target collection name (optional).
    """

    text: str
    top_k: int = 10
    score_threshold: float | None = None
    include_metadata: bool = True
    filter: dict[str, Any] | None = None
    collection: str | None = None


@dataclass
class RetrievedChunk:
    """A single chunk returned by the retrieval pipeline.

    Attributes:
        chunk_id: Unique chunk identifier.
        content: The chunk text content.
        score: Relevance score (higher = more relevant).
        metadata: Arbitrary metadata attached to the chunk.
        document_id: Optional parent document identifier.
    """

    chunk_id: str = ""
    content: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    document_id: str | None = None


@dataclass
class RetrievalMetadata:
    """Metadata about a retrieval operation.

    Attributes:
        query_text: The original query.
        retriever_name: Name of the retriever used.
        reranker_name: Name of the reranker used.
        num_candidates: Number of candidates before reranking.
        total_time: Total wall-clock time in seconds.
        collection: Collection queried.
        retrieved_at: Timestamp of retrieval.
    """

    query_text: str = ""
    retriever_name: str = ""
    reranker_name: str = ""
    num_candidates: int = 0
    total_time: float = 0.0
    collection: str = ""
    retrieved_at: datetime | None = None


@dataclass
class RetrievalStatistics:
    """Aggregate statistics for a retrieval run.

    Attributes:
        latency: Total latency in seconds.
        recall: Recall@k (if ground truth available).
        precision: Precision@k.
        mrr: Mean Reciprocal Rank.
        ndcg: Normalised Discounted Cumulative Gain.
        top_k_hit_rate: Fraction of queries with at least one relevant result.
        throughput: Queries per second.
        num_queries: Number of queries processed.
    """

    latency: float = 0.0
    recall: float = 0.0
    precision: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    top_k_hit_rate: float = 0.0
    throughput: float = 0.0
    num_queries: int = 0


@dataclass
class RetrievalResult:
    """The complete output of a retrieval pipeline run.

    Attributes:
        chunks: The retrieved chunks, sorted by score (best first).
        query: The original search query.
        metadata: Operation metadata.
        statistics: Aggregate statistics.
        warnings: Non-fatal warnings.
        errors: Fatal errors.
        successful: Whether the run completed without fatal error.
    """

    chunks: list[RetrievedChunk] = field(default_factory=list)
    query: SearchQuery | None = None
    metadata: RetrievalMetadata = field(default_factory=RetrievalMetadata)
    statistics: RetrievalStatistics = field(default_factory=RetrievalStatistics)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    successful: bool = True
