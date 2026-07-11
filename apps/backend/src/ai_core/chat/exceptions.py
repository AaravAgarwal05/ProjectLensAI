"""Chat engine exceptions."""

from __future__ import annotations


class ChatError(Exception):
    """Base exception for chat engine errors."""


class SessionNotFoundError(ChatError):
    """Raised when a session ID is not found."""


class MessageNotFoundError(ChatError):
    """Raised when a message ID is not found."""


class EmptyMessageError(ChatError):
    """Raised when a message is empty or whitespace-only."""


class MessageTooLongError(ChatError):
    """Raised when a message exceeds the maximum length."""


class MaxHistoryExceededError(ChatError):
    """Raised when conversation history exceeds limits."""


class SessionArchivedError(ChatError):
    """Raised when trying to interact with an archived session."""


class StreamingFailedError(ChatError):
    """Raised when streaming generation fails."""


class InvalidModeError(ChatError):
    """Raised when an invalid chat mode is specified."""
