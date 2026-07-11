"""Tests for context strategies."""

import pytest

from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import ContextChunk
from src.ai_core.context.strategies.comparison import ComparisonStrategy
from src.ai_core.context.strategies.multi_document import MultiDocumentStrategy
from src.ai_core.context.strategies.single_document import SingleDocumentStrategy
from src.ai_core.context.strategies.summary import SummaryStrategy


class TestSingleDocumentStrategy:
    @pytest.fixture
    def strategy(self):
        return SingleDocumentStrategy()

    @pytest.mark.asyncio
    async def test_assemble_basic(self, strategy):
        ctx = await strategy.assemble(
            query="test query",
            chunks=[ContextChunk(chunk_id="c1", content="content", score=0.9)],
            history=[],
            config=ContextConfiguration.default(),
        )
        assert ctx.query == "test query"
        assert len(ctx.chunks) == 1
        assert ctx.successful is True

    @pytest.mark.asyncio
    async def test_assemble_empty_chunks(self, strategy):
        ctx = await strategy.assemble(
            query="q", chunks=[], history=[], config=ContextConfiguration.default()
        )
        assert ctx.chunks == []
        assert ctx.query == "q"

    @pytest.mark.asyncio
    async def test_strategy_name(self, strategy):
        assert strategy.strategy_name == "single_document"

    def test_configure(self, strategy):
        strategy.configure({"system_prompt": "custom"})
        assert strategy._system_prompt == "custom"


class TestMultiDocumentStrategy:
    @pytest.fixture
    def strategy(self):
        return MultiDocumentStrategy()

    @pytest.mark.asyncio
    async def test_assemble_multi_source(self, strategy):
        chunks = [
            ContextChunk(chunk_id="c1", content="a", score=0.9, source_id="doc1"),
            ContextChunk(chunk_id="c2", content="b", score=0.8, source_id="doc2"),
            ContextChunk(chunk_id="c3", content="c", score=0.7, source_id="doc1"),
        ]
        ctx = await strategy.assemble(
            query="q", chunks=chunks, history=[], config=ContextConfiguration.default()
        )
        assert len(ctx.chunks) == 3
        assert ctx.metadata.strategy == "multi_document"

    @pytest.mark.asyncio
    async def test_per_doc_limit(self, strategy):
        chunks = [
            ContextChunk(chunk_id=f"c{i}", content="x", score=0.9, source_id="doc1")
            for i in range(20)
        ]
        ctx = await strategy.assemble(
            query="q", chunks=chunks, history=[], config=ContextConfiguration.default()
        )
        assert len(ctx.chunks) == 10  # default max_chunks_per_doc

    @pytest.mark.asyncio
    async def test_strategy_name(self, strategy):
        assert strategy.strategy_name == "multi_document"

    def test_configure(self, strategy):
        strategy.configure({"max_chunks_per_doc": 5})
        assert strategy._max_chunks_per_doc == 5


class TestComparisonStrategy:
    @pytest.fixture
    def strategy(self):
        return ComparisonStrategy()

    @pytest.mark.asyncio
    async def test_assemble_comparison(self, strategy):
        chunks = [
            ContextChunk(chunk_id="c1", content="a", score=0.9, source_id="doc1"),
            ContextChunk(chunk_id="c2", content="b", score=0.8, source_id="doc2"),
            ContextChunk(chunk_id="c3", content="c", score=0.7, source_id="doc1"),
        ]
        ctx = await strategy.assemble(
            query="compare", chunks=chunks, history=[], config=ContextConfiguration.default()
        )
        assert len(ctx.chunks) >= 2
        assert ctx.metadata.strategy == "comparison"

    @pytest.mark.asyncio
    async def test_strategy_name(self, strategy):
        assert strategy.strategy_name == "comparison"


class TestSummaryStrategy:
    @pytest.fixture
    def strategy(self):
        return SummaryStrategy()

    @pytest.mark.asyncio
    async def test_assemble_summary(self, strategy):
        chunks = [
            ContextChunk(chunk_id="c1", content="long content here", score=0.9),
            ContextChunk(chunk_id="c2", content="more content", score=0.8),
        ]
        ctx = await strategy.assemble(
            query="summarize", chunks=chunks, history=[], config=ContextConfiguration.default()
        )
        assert len(ctx.chunks) == 1  # condensed into single chunk
        assert ctx.chunks[0].chunk_id == "summary_combined"

    @pytest.mark.asyncio
    async def test_empty_chunks(self, strategy):
        ctx = await strategy.assemble(
            query="q", chunks=[], history=[], config=ContextConfiguration.default()
        )
        assert ctx.chunks == []

    @pytest.mark.asyncio
    async def test_strategy_name(self, strategy):
        assert strategy.strategy_name == "summary"
