"""Embedding-specific exceptions."""


class EmbeddingError(Exception):
    """Base embedding exception."""


class ProviderNotFoundError(EmbeddingError):
    """Raised when a provider name is not registered."""


class EmbeddingValidationError(EmbeddingError):
    """Raised when validation fails."""


class ModelNotAvailableError(EmbeddingError):
    """Raised when the requested model is not available on the provider."""


class ProviderConnectionError(EmbeddingError):
    """Raised when the provider cannot be reached."""
