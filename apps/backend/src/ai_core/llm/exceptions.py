"""LLM engine exceptions."""

from __future__ import annotations


class LLMError(Exception):
    """Base exception for LLM engine errors."""


class ProviderNotFoundError(LLMError):
    """Raised when no provider matches the requested name."""


class ProviderNotAvailableError(LLMError):
    """Raised when a provider is registered but not reachable."""


class ModelNotFoundError(LLMError):
    """Raised when a model is not available on the provider."""


class GenerationError(LLMError):
    """Raised when text generation fails."""


class StreamingError(GenerationError):
    """Raised when streaming generation fails."""


class TimeoutError(LLMError):
    """Raised when a generation request times out."""


class EmptyResponseError(LLMError):
    """Raised when the provider returns an empty response."""


class HallucinatedCitationError(LLMError):
    """Raised when a response contains a citation not in the source context."""


class TokenLimitExceededError(LLMError):
    """Raised when token counts exceed configured limits."""


class ConfigurationError(LLMError):
    """Raised on invalid or incomplete configuration."""
