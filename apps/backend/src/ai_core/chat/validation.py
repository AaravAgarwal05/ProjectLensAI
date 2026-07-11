"""Validation for chat operations."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.ai_core.chat.exceptions import (
    EmptyMessageError,
    MessageTooLongError,
    SessionArchivedError,
    SessionNotFoundError,
)
from src.ai_core.chat.models import ChatSession, CitationReference

logger = logging.getLogger(__name__)


@dataclass
class ChatValidationResult:
    """Result of a validation check."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ChatValidationEngine:
    """Validates chat inputs, sessions, and responses."""

    def __init__(self, max_message_length: int = 10000) -> None:
        self._max_message_length = max_message_length

    # ------------------------------------------------------------------
    # Message validation
    # ------------------------------------------------------------------

    def validate_message(self, message: str) -> None:
        """Validate a user message. Raises on invalid input."""
        if not message or not message.strip():
            raise EmptyMessageError("Message cannot be empty")

        if len(message) > self._max_message_length:
            raise MessageTooLongError(
                f"Message exceeds {self._max_message_length} characters " f"({len(message)} given)"
            )

    def validate_session_active(self, session: ChatSession | None) -> None:
        """Validate a session exists and is not archived."""
        if session is None:
            raise SessionNotFoundError("Session not found")
        if session.archived:
            raise SessionArchivedError("Session is archived")

    # ------------------------------------------------------------------
    # Session validation
    # ------------------------------------------------------------------

    def validate_session_mode(self, mode: str) -> None:
        """Validate chat mode."""
        valid_modes = {"single", "multi", "comparison"}
        if mode not in valid_modes:
            from src.ai_core.chat.exceptions import InvalidModeError

            raise InvalidModeError(
                f"Invalid mode '{mode}'. Must be one of: {', '.join(sorted(valid_modes))}"
            )

    # ------------------------------------------------------------------
    # Citation validation
    # ------------------------------------------------------------------

    def validate_citations(
        self,
        citations: list[CitationReference],
        response_text: str,
    ) -> ChatValidationResult:
        """Check citation consistency with response text."""
        result = ChatValidationResult(valid=True)

        if not citations:
            result.warnings.append("No citations provided with response")
            return result

        for citation in citations:
            title_lower = citation.report_title.lower()
            if title_lower and title_lower not in response_text.lower():
                result.warnings.append(
                    f"Citation '{citation.report_title}' not found verbatim in response"
                )

        return result

    # ------------------------------------------------------------------
    # Streaming validation
    # ------------------------------------------------------------------

    def validate_streaming_params(self, session_id: str, message: str) -> None:
        """Validate streaming parameters."""
        self.validate_message(message)
        if not session_id:
            raise ValueError("session_id is required for streaming")
