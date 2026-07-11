"""Tests for reranker registry, factory, and providers."""

import pytest

from src.ai_core.retrieval.exceptions import RerankerNotFoundError
from src.ai_core.retrieval.models import RetrievedChunk, SearchQuery
from src.ai_core.retrieval.reranking.base import Reranker
from src.ai_core.retrieval.reranking.factory import RerankerFactory
from src.ai_core.retrieval.reranking.providers.cross_encoder import CrossEncoderReranker
from src.ai_core.retrieval.reranking.providers.no_reranker import NoReranker
from src.ai_core.retrieval.reranking.registry import RerankerRegistry


class _FakeReranker(Reranker):
    @property
    def reranker_name(self) -> str:
        return "fake"

    async def rerank(
        self, query: SearchQuery, candidates: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        return candidates

    def configure(self, params: dict) -> None:
        pass


class TestRerankerRegistry:
    def test_register_and_get(self):
        reg = RerankerRegistry()
        reg.register("fake", _FakeReranker)
        r = reg.get("fake")
        assert r.reranker_name == "fake"

    def test_get_unknown(self):
        reg = RerankerRegistry()
        with pytest.raises(RerankerNotFoundError):
            reg.get("nonexistent")

    def test_lazy_instantiation(self):
        reg = RerankerRegistry()
        reg.register("fake", _FakeReranker)
        s1 = reg.get("fake")
        s2 = reg.get("fake")
        assert s1 is s2

    def test_unregister(self):
        reg = RerankerRegistry()
        reg.register("fake", _FakeReranker)
        reg.unregister("fake")
        assert "fake" not in reg.list_names()


class TestRerankerFactory:
    def test_create(self):
        factory = RerankerFactory()
        factory.registry.register("fake", _FakeReranker)
        r = factory.create("fake")
        assert isinstance(r, _FakeReranker)

    def test_create_unknown(self):
        factory = RerankerFactory()
        with pytest.raises(RerankerNotFoundError):
            factory.create("unknown")

    def test_create_with_aliases(self):
        factory = RerankerFactory()
        factory.registry.register("none", _FakeReranker)
        r = factory.create("default")
        assert isinstance(r, _FakeReranker)


class TestNoReranker:
    @pytest.fixture
    def reranker(self):
        return NoReranker()

    async def test_passthrough(self, reranker):
        chunks = [
            RetrievedChunk(chunk_id="c1", content="a", score=0.9),
            RetrievedChunk(chunk_id="c2", content="b", score=0.8),
        ]
        query = SearchQuery(text="test")
        result = await reranker.rerank(query, chunks)
        assert result is chunks
        assert len(result) == 2

    async def test_empty_input(self, reranker):
        query = SearchQuery(text="test")
        result = await reranker.rerank(query, [])
        assert result == []

    def test_name(self, reranker):
        assert reranker.reranker_name == "none"


class TestCrossEncoderReranker:
    @pytest.fixture
    def reranker(self):
        return CrossEncoderReranker(model_name="mock-model")

    def test_name(self, reranker):
        assert reranker.reranker_name == "cross_encoder"

    async def test_graceful_unavailable(self, reranker):
        """Without a real cross-encoder model, it should return candidates unchanged."""
        chunks = [
            RetrievedChunk(chunk_id="c1", content="test content", score=0.9),
        ]
        query = SearchQuery(text="test")
        result = await reranker.rerank(query, chunks)
        assert len(result) == 1
        assert result[0].chunk_id == "c1"

    async def test_empty_candidates(self, reranker):
        query = SearchQuery(text="test")
        result = await reranker.rerank(query, [])
        assert result == []

    def test_configure(self):
        r = CrossEncoderReranker()
        r.configure({"model_name": "other-model"})
        assert r._model_name == "other-model"
        assert r._model is None
