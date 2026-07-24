"""Tests for ContextAssemblyPipeline."""

import pytest

from src.ai_core.context.base import ContextStrategy
from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.hooks import ContextHookEvent
from src.ai_core.context.models import (
    ContextChunk,
    ConversationMessage,
    LLMContext,
)
from src.ai_core.context.pipeline import ContextAssemblyPipeline


class _SimpleStrategy(ContextStrategy):
    @property
    def strategy_name(self) -> str:
        return "simple"

    async def assemble(self, query, chunks, history, config):
        return LLMContext(
            query=query,
            chunks=chunks,
            conversation_history=history,
        )

    def configure(self, params: dict) -> None:
        pass


class TestContextAssemblyPipeline:
    @pytest.fixture
    def pipeline(self):
        return ContextAssemblyPipeline(strategy=_SimpleStrategy())

    @pytest.mark.asyncio
    async def test_basic_assembly(self, pipeline):
        ctx = await pipeline.run(
            query="test query",
            chunks=[ContextChunk(chunk_id="c1", content="test content", score=0.9)],
        )
        assert ctx.query == "test query"
        assert len(ctx.chunks) == 1
        assert ctx.successful is True

    @pytest.mark.asyncio
    async def test_empty_query(self, pipeline):
        ctx = await pipeline.run(query="", chunks=[])
        assert ctx.query == ""

    @pytest.mark.asyncio
    async def test_with_history(self, pipeline):
        ctx = await pipeline.run(
            query="q",
            chunks=[],
            history=[ConversationMessage(role="user", content="previous question")],
        )
        assert len(ctx.conversation_history) == 1
        assert ctx.conversation_history[0].content == "previous question"

    @pytest.mark.asyncio
    async def test_with_extra_metadata(self, pipeline):
        ctx = await pipeline.run(
            query="q",
            chunks=[ContextChunk(chunk_id="c1", content="test")],
            extra_metadata={"report_title": "Annual Report"},
        )
        assert ctx.chunks[0].source_title == "Annual Report"

    @pytest.mark.asyncio
    async def test_hooks(self, pipeline):
        events: list[str] = []

        async def before_hook(q, c, h):
            events.append("before")
            return q, c, h

        async def after_hook(ctx):
            events.append("after")
            return ctx

        pipeline._hooks.register(ContextHookEvent.BEFORE_CONTEXT, before_hook, name="before")
        pipeline._hooks.register(ContextHookEvent.AFTER_CONTEXT, after_hook, name="after")

        await pipeline.run(query="q", chunks=[])
        assert "before" in events
        assert "after" in events

    @pytest.mark.asyncio
    async def test_metadata_populated(self, pipeline):
        ctx = await pipeline.run(
            query="test query",
            chunks=[ContextChunk(chunk_id="c1", content="x", score=0.9)],
        )
        assert ctx.metadata.query_text == "test query"
        assert ctx.metadata.num_chunks == 1
        assert ctx.metadata.assembly_time > 0
        assert ctx.metadata.total_tokens > 0

    @pytest.mark.asyncio
    async def test_statistics(self, pipeline):
        ctx = await pipeline.run(
            query="q",
            chunks=[ContextChunk(chunk_id="c1", content="x")],
        )
        assert ctx.statistics.context_size >= 1
        assert ctx.statistics.assembly_latency > 0

    @pytest.mark.asyncio
    async def test_budget_enforced(self, pipeline):
        small_cfg = ContextConfiguration(max_tokens=256)
        long_chunks = [ContextChunk(chunk_id=f"c{i}", content="content " * 100) for i in range(10)]
        ctx = await pipeline.run(query="q", chunks=long_chunks, config=small_cfg)
        assert ctx.budget.total == 256

    @pytest.mark.asyncio
    async def test_configure(self, pipeline):
        pipeline.configure({"strategy": {"system_prompt": "custom"}})
        assert isinstance(pipeline._strategy, _SimpleStrategy)
