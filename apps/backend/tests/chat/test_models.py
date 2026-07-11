"""Tests for chat data models."""

from datetime import UTC, datetime

from src.ai_core.chat.models import (
    ChatMessage,
    ChatMetadata,
    ChatSession,
    CitationReference,
    MessageRole,
    SessionStatistics,
)


class TestMessageRole:
    def test_values(self):
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"


class TestCitationReference:
    def test_defaults(self):
        c = CitationReference()
        assert c.report_id == ""
        assert c.score == 0.0
        assert c.page_number is None

    def test_full(self):
        c = CitationReference(
            report_id="r1",
            report_title="Doc",
            page_number=10,
            section_name="Intro",
            chunk_id="c1",
            score=0.95,
        )
        assert c.report_id == "r1"
        assert c.section_name == "Intro"
        assert c.score == 0.95


class TestChatMessage:
    def test_defaults(self):
        m = ChatMessage()
        assert m.role == "user"
        assert m.content == ""
        assert m.citations == []
        assert m.metadata == {}

    def test_with_values(self):
        now = datetime.now(UTC)
        citations = [CitationReference(report_id="r1")]
        m = ChatMessage(
            id="msg1",
            session_id="s1",
            role="assistant",
            content="Hello",
            citations=citations,
            metadata={"key": "val"},
            created_at=now,
        )
        assert m.content == "Hello"
        assert m.citations[0].report_id == "r1"
        assert m.metadata["key"] == "val"


class TestChatSession:
    def test_defaults(self):
        s = ChatSession()
        assert s.report_ids == []
        assert s.mode == "single"
        assert s.archived is False

    def test_with_values(self):
        now = datetime.now(UTC)
        s = ChatSession(
            id="s1",
            title="Test",
            report_ids=["r1", "r2"],
            mode="multi",
            created_at=now,
            updated_at=now,
        )
        assert s.title == "Test"
        assert len(s.report_ids) == 2
        assert s.mode == "multi"


class TestChatMetadata:
    def test_defaults(self):
        m = ChatMetadata()
        assert m.total_sessions == 0

    def test_values(self):
        m = ChatMetadata(total_sessions=10, total_messages=50, active_sessions=3)
        assert m.total_messages == 50


class TestSessionStatistics:
    def test_defaults(self):
        s = SessionStatistics()
        assert s.average_response_time == 0.0

    def test_values(self):
        s = SessionStatistics(
            message_count=10,
            token_count=500,
            citation_count=15,
            average_response_time=1.5,
        )
        assert s.token_count == 500
