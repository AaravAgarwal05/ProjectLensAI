"""Tests for RetrievalPipeline."""

import pytest

from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.hooks import RetrievalHookEvent, RetrievalHookRegistry
from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk, SearchQuery
from src.ai_core.retrieval.pipeline import RetrievalPipeline
from src.ai_core.retrieval.reranking.base import Reranker


class _SimpleRetriever(Retriever):
    @property
    def retriever_name(self) -> str:
        return "simple"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        return RetrievalResult(
            chunks=[
                RetrievedChunk(chunk_id="c1", content="a", score=0.9),
                RetrievedChunk(chunk_id="c2", content="b", score=0.7),
            ],
            successful=True,
        )

    def configure(self, params: dict) -> None:
        pass


class _EmptyRetriever(Retriever):
    @property
    def retriever_name(self) -> str:
        return "empty"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        return RetrievalResult(chunks=[], successful=True)

    def configure(self, params: dict) -> None:
        pass


class _ErrorRetriever(Retriever):
    @property
    def retriever_name(self) -> str:
        return "error"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        msg = "Connection failed"
        raise ConnectionError(msg)

    def configure(self, params: dict) -> None:
        pass


class _ScoresUpReranker(Reranker):
    @property
    def reranker_name(self) -> str:
        return "scores_up"

    async def rerank(
        self, query: SearchQuery, candidates: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        for c in candidates:
            c.score += 0.1
        return candidates

    def configure(self, params: dict) -> None:
        pass


class _CrashReranker(Reranker):
    @property
    def reranker_name(self) -> str:
        return "crash"

    async def rerank(
        self, query: SearchQuery, candidates: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        raise RuntimeError("reranker crashed")

    def configure(self, params: dict) -> None:
        pass


class TestRetrievalPipeline:
    @pytest.fixture
    def pipeline(self):
        return RetrievalPipeline(retriever=_SimpleRetriever())

    async def test_basic_retrieval(self, pipeline):
        query = SearchQuery(text="test query")
        result = await pipeline.run(query)
        assert result.successful is True
        assert len(result.chunks) == 2
        assert result.chunks[0].score >= result.chunks[1].score

    async def test_empty_query(self, pipeline):
        query = SearchQuery(text="")
        result = await pipeline.run(query)
        assert result.successful is False

    async def test_empty_results(self):
        pipeline = RetrievalPipeline(retriever=_EmptyRetriever())
        query = SearchQuery(text="test")
        result = await pipeline.run(query)
        assert result.chunks == []

    async def test_retrieval_error(self):
        pipeline = RetrievalPipeline(retriever=_ErrorRetriever())
        query = SearchQuery(text="test")
        result = await pipeline.run(query)
        assert result.successful is False
        assert any("Connection" in e for e in result.errors)

    async def test_with_reranker(self):
        pipeline = RetrievalPipeline(
            retriever=_SimpleRetriever(),
            reranker=_ScoresUpReranker(),
        )
        query = SearchQuery(text="test")
        result = await pipeline.run(query)
        assert result.chunks[0].score > 0.9

    async def test_reranker_crash_continues(self):
        pipeline = RetrievalPipeline(
            retriever=_SimpleRetriever(),
            reranker=_CrashReranker(),
        )
        query = SearchQuery(text="test")
        result = await pipeline.run(query)
        # Pipeline should continue with warning, not fail
        assert result.successful is True
        assert len(result.warnings) > 0

    async def test_hooks(self):
        registry = RetrievalHookRegistry()
        events: list[str] = []

        async def record_before(q: SearchQuery) -> SearchQuery:
            events.append("before")
            return q

        async def record_after(chunks: list) -> list:
            events.append("after")
            return chunks

        registry.register(RetrievalHookEvent.BEFORE_RETRIEVAL, record_before, name="before")
        registry.register(RetrievalHookEvent.AFTER_RETRIEVAL, record_after, name="after")

        pipeline = RetrievalPipeline(retriever=_SimpleRetriever(), hooks=registry)
        query = SearchQuery(text="test")
        await pipeline.run(query)
        assert "before" in events
        assert "after" in events

    async def test_metadata_populated(self, pipeline):
        query = SearchQuery(text="test query")
        result = await pipeline.run(query)
        assert result.metadata.retriever_name == "simple"
        assert result.metadata.query_text == "test query"
        assert result.metadata.total_time > 0
        assert result.metadata.num_candidates == 2
