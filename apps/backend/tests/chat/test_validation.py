"""Tests for ChatValidationEngine."""

from __future__ import annotations

import pytest

from src.ai_core.chat.exceptions import (
    EmptyMessageError,
    InvalidModeError,
    MessageTooLongError,
    SessionArchivedError,
    SessionNotFoundError,
)
from src.ai_core.chat.models import ChatSession, CitationReference
from src.ai_core.chat.validation import ChatValidationEngine


class TestChatValidationEngine:
    def setup_method(self):
        self.engine = ChatValidationEngine(max_message_length=100)

    # -- Message validation --

    def test_validate_message_valid(self):
        # Should not raise
        self.engine.validate_message("Hello")

    def test_validate_message_empty_string(self):
        with pytest.raises(EmptyMessageError):
            self.engine.validate_message("")

    def test_validate_message_whitespace_only(self):
        with pytest.raises(EmptyMessageError):
            self.engine.validate_message("   \n  ")

    def test_validate_message_too_long(self):
        with pytest.raises(MessageTooLongError):
            self.engine.validate_message("x" * 101)

    def test_validate_message_at_max_length(self):
        # Should not raise
        self.engine.validate_message("x" * 100)

    # -- Session validation --

    def test_validate_session_active_valid(self):
        session = ChatSession(id="s1", archived=False)
        self.engine.validate_session_active(session)

    def test_validate_session_active_none(self):
        with pytest.raises(SessionNotFoundError):
            self.engine.validate_session_active(None)

    def test_validate_session_active_archived(self):
        session = ChatSession(id="s1", archived=True)
        with pytest.raises(SessionArchivedError):
            self.engine.validate_session_active(session)

    # -- Mode validation --

    def test_validate_session_mode_valid_single(self):
        self.engine.validate_session_mode("single")

    def test_validate_session_mode_valid_multi(self):
        self.engine.validate_session_mode("multi")

    def test_validate_session_mode_valid_comparison(self):
        self.engine.validate_session_mode("comparison")

    def test_validate_session_mode_invalid(self):
        with pytest.raises(InvalidModeError):
            self.engine.validate_session_mode("invalid")

    # -- Citation validation --

    def test_validate_citations_empty(self):
        result = self.engine.validate_citations([], "response text")
        assert result.valid is True
        assert "No citations provided" in result.warnings[0]

    def test_validate_citations_all_present(self):
        citations = [
            CitationReference(report_id="r1", report_title="Technical Report"),
        ]
        result = self.engine.validate_citations(citations, "This is from the Technical Report.")
        assert result.valid is True
        assert len(result.warnings) == 0

    def test_validate_citations_title_not_in_response(self):
        citations = [
            CitationReference(report_id="r1", report_title="Missing Report"),
        ]
        result = self.engine.validate_citations(citations, "Response without the title.")
        assert result.valid is True
        assert len(result.warnings) == 1
        assert "Missing Report" in result.warnings[0]

    def test_validate_citations_case_insensitive(self):
        citations = [
            CitationReference(report_id="r1", report_title="Technical REPORT"),
        ]
        result = self.engine.validate_citations(citations, "This is from the technical report.")
        assert result.valid is True
        assert len(result.warnings) == 0

    # -- Streaming params --

    def test_validate_streaming_params_valid(self):
        self.engine.validate_streaming_params("session-1", "Hello")

    def test_validate_streaming_params_empty_session(self):
        with pytest.raises(ValueError):
            self.engine.validate_streaming_params("", "Hello")

    def test_validate_streaming_params_empty_message(self):
        with pytest.raises(EmptyMessageError):
            self.engine.validate_streaming_params("session-1", "")
