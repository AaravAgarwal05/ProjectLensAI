"""Context manager exception classes."""

from __future__ import annotations


class ContextError(Exception):
    """Base exception for context operations."""


class StrategyNotFoundError(ContextError):
    """Raised when no strategy is registered under a name."""


class BudgetExceededError(ContextError):
    """Raised when token budget cannot accommodate content."""


class EmptyContextError(ContextError):
    """Raised when assembled context has no content."""


class MissingMetadataError(ContextError):
    """Raised when required metadata is missing."""


class ValidationError(ContextError):
    """Raised when context validation fails."""


class ConfigurationError(ContextError):
    """Raised when configuration is invalid."""
