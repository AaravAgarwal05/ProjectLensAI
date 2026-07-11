"""Tests for PromptBuilder."""

from src.ai_core.context.models import (
    ContextChunk,
    ContextMetadata,
    ConversationMessage,
    ConversationSummary,
    LLMContext,
)
from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.prompt_builder import PromptBuilder


class TestPromptBuilder:
    def test_build_minimal(self):
        """Build from empty context."""
        builder = PromptBuilder()
        ctx = LLMContext()
        request = builder.build(ctx)
        assert request.system_prompt != ""
        assert request.user_prompt == ""
        assert request.temperature == 0.7

    def test_build_with_query(self):
        """Build from context with query."""
        builder = PromptBuilder()
        ctx = LLMContext(query="What is ProjectLens?")
        request = builder.build(ctx)
        assert "ProjectLens" in request.user_prompt

    def test_build_with_chunks(self):
        """Build with context chunks."""
        builder = PromptBuilder()
        chunks = [
            ContextChunk(
                chunk_id="c1",
                content="ProjectLens is an AI platform.",
                source_title="Docs",
                section_name="Overview",
                citations=["doc_1"],
            ),
        ]
        ctx = LLMContext(query="Tell me about it", chunks=chunks)
        request = builder.build(ctx)
        assert "ProjectLens" in request.user_prompt
        assert "[Chunk 1]" in request.user_prompt
        assert "Overview" in request.user_prompt
        assert "Docs" in request.user_prompt
        assert "doc_1" in request.metadata["citations"]

    def test_build_with_history(self):
        """Build with conversation history."""
        builder = PromptBuilder()
        history = [
            ConversationMessage(role="user", content="Hi"),
            ConversationMessage(role="assistant", content="Hello!"),
        ]
        ctx = LLMContext(query="What next?", conversation_history=history)
        request = builder.build(ctx)
        assert "Hi" in request.user_prompt
        assert "Hello!" in request.user_prompt

    def test_build_with_summary(self):
        """Build with conversation summary."""
        builder = PromptBuilder()
        ctx = LLMContext(
            query="Continue",
            conversation_summary=ConversationSummary(
                text="User asked about features",
                message_count=3,
            ),
        )
        request = builder.build(ctx)
        assert "features" in request.user_prompt
        assert "summary" in request.user_prompt.lower()

    def test_system_prompt_includes_metadata(self):
        """System prompt should include context metadata."""
        builder = PromptBuilder()
        ctx = LLMContext(
            query="test",
            system_prompt="Custom system prompt.",
            metadata=ContextMetadata(
                strategy="single_document",
                num_chunks=5,
                num_messages=2,
            ),
        )
        request = builder.build(ctx)
        assert "Custom system prompt." in request.system_prompt
        assert "single_document" in request.system_prompt
        assert "Context chunks: 5" in request.system_prompt

    def test_build_with_overrides(self):
        """Build with temperature/model overrides."""
        builder = PromptBuilder()
        ctx = LLMContext(query="test")
        request = builder.build(ctx, overrides={"temperature": 0.1, "model_name": "custom"})
        assert request.temperature == 0.1
        assert request.model_name == "custom"

    def test_custom_system_prompt_default(self):
        """Use configured system prompt when context has none."""
        config = LLMConfiguration(system_prompt="Custom default system prompt.")
        builder = PromptBuilder(config)
        ctx = LLMContext(query="hi")
        request = builder.build(ctx)
        assert "Custom default system prompt." in request.system_prompt

    def test_collect_citations(self):
        """Collect unique citations from chunks."""
        builder = PromptBuilder()
        chunks = [
            ContextChunk(chunk_id="c1", content="a", citations=["src_1", "src_2"]),
            ContextChunk(chunk_id="c2", content="b", citations=["src_2", "src_3"]),
        ]
        ctx = LLMContext(query="q", chunks=chunks)
        request = builder.build(ctx)
        assert request.metadata["citations"] == ["src_1", "src_2", "src_3"]
