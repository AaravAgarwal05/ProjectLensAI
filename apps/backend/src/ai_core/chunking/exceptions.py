"""Chunking-specific exceptions."""


class ChunkingError(Exception):
    """Base chunking exception."""


class ChunkerNotFoundError(ChunkingError):
    """Raised when a strategy name is not registered."""


class ChunkingValidationError(ChunkingError):
    """Raised when validation fails."""


class DocumentEmptyError(ChunkingError):
    """Raised when the parsed document has no text content."""
