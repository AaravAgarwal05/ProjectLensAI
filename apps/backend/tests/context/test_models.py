"""Tests for context models."""

from src.ai_core.context.models import (
    ContextBudget,
    ContextChunk,
    ContextMetadata,
    ContextRole,
    ContextStatistics,
    ConversationMessage,
    ConversationSummary,
    LLMContext,
)


class TestConversationMessage:
    def test_minimal(self):
        msg = ConversationMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_with_role_enum(self):
        msg = ConversationMessage(role=ContextRole.USER, content="test")
        assert msg.role == "user"

    def test_with_metadata(self):
        msg = ConversationMessage(role="assistant", content="reply", metadata={"key": "val"})
        assert msg.metadata["key"] == "val"


class TestConversationSummary:
    def test_defaults(self):
        s = ConversationSummary(text="summary")
        assert s.text == "summary"
        assert s.token_count == 0
        assert s.message_count == 0

    def test_custom(self):
        s = ConversationSummary(text="s", token_count=50, message_count=3)
        assert s.token_count == 50
        assert s.message_count == 3


class TestContextChunk:
    def test_minimal(self):
        c = ContextChunk(chunk_id="c1", content="content")
        assert c.chunk_id == "c1"
        assert c.score == 0.0
        assert c.citations == []

    def test_with_metadata(self):
        c = ContextChunk(
            chunk_id="c1",
            content="x",
            score=0.9,
            source_id="src1",
            source_title="Doc",
            page_number=5,
            section_name="Intro",
            token_count=100,
            citations=["src1"],
        )
        assert c.score == 0.9
        assert c.page_number == 5
        assert c.section_name == "Intro"


class TestContextBudget:
    def test_defaults(self):
        b = ContextBudget()
        assert b.total == 0
        assert b.allocated == 0
        assert b.remaining == 0

    def test_allocation(self):
        b = ContextBudget(
            total=1000,
            system_prompt=200,
            user_query=50,
            conversation_history=300,
            retrieved_chunks=400,
            reserved=50,
        )
        assert b.allocated == 1000
        assert b.remaining == 0

    def test_remaining(self):
        b = ContextBudget(total=1000, system_prompt=200)
        assert b.remaining == 800


class TestContextMetadata:
    def test_defaults(self):
        m = ContextMetadata()
        assert m.query_text == ""
        assert m.num_chunks == 0


class TestContextStatistics:
    def test_defaults(self):
        s = ContextStatistics()
        assert s.context_size == 0
        assert s.assembly_latency == 0.0


class TestLLMContext:
    def test_defaults(self):
        ctx = LLMContext()
        assert ctx.successful is True
        assert ctx.chunks == []
        assert ctx.warnings == []

    def test_with_chunks(self):
        chunks = [ContextChunk(chunk_id="c1", content="a")]
        ctx = LLMContext(query="q", chunks=chunks)
        assert len(ctx.chunks) == 1
        assert ctx.query == "q"

    def test_full_text_empty(self):
        ctx = LLMContext()
        assert ctx.full_text == ""

    def test_full_text_with_content(self):
        ctx = LLMContext(
            query="test query",
            system_prompt="You are a helpful assistant.",
            chunks=[
                ContextChunk(chunk_id="c1", content="chunk content", section_name="Results"),
            ],
        )
        text = ctx.full_text
        assert "test query" in text
        assert "helpful assistant" in text
        assert "chunk content" in text
        assert "[Results]" in text

    def test_full_text_with_history(self):
        ctx = LLMContext(
            query="q",
            conversation_history=[
                ConversationMessage(role="user", content="hi"),
            ],
        )
        text = ctx.full_text
        assert "user: hi" in text
