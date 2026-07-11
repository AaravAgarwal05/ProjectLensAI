"""Retrieval exception classes."""

from __future__ import annotations


class RetrievalError(Exception):
    """Base exception for retrieval operations."""


class RetrieverNotFoundError(RetrievalError):
    """Raised when no retriever is registered under a name."""


class RerankerNotFoundError(RetrievalError):
    """Raised when no reranker is registered under a name."""


class EmbeddingError(RetrievalError):
    """Raised when query embedding fails."""


class SearchError(RetrievalError):
    """Raised when vector search fails."""


class EmptyQueryError(RetrievalError):
    """Raised when the query text is empty."""


class ScoreThresholdNotMetError(RetrievalError):
    """Raised when no results meet the score threshold."""
