"""Vector-store exception classes."""

from __future__ import annotations


class VectorStoreError(Exception):
    """Base exception for vector-store operations."""


class CollectionNotFoundError(VectorStoreError):
    """Raised when a collection does not exist."""


class DocumentNotFoundError(VectorStoreError):
    """Raised when a document is not found."""


class DimensionMismatchError(VectorStoreError):
    """Raised when vector dimensions don't match the collection."""


class StoreConnectionError(VectorStoreError):
    """Raised when the store cannot be reached."""


class StoreNotFoundError(VectorStoreError):
    """Raised when no store is registered under a given name."""
