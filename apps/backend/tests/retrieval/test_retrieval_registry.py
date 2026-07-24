"""Tests for retriever registry and factory."""

import pytest

from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.configuration import RetrieverConfiguration
from src.ai_core.retrieval.exceptions import RetrieverNotFoundError
from src.ai_core.retrieval.factory import RetrieverFactory
from src.ai_core.retrieval.models import RetrievalResult, SearchQuery
from src.ai_core.retrieval.registry import RetrieverRegistry


class _FakeRetriever(Retriever):
    @property
    def retriever_name(self) -> str:
        return "fake"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        return RetrievalResult()

    def configure(self, params: dict) -> None:
        pass


class TestRetrieverRegistry:
    def test_register_and_get(self):
        reg = RetrieverRegistry()
        reg.register("fake", _FakeRetriever)
        r = reg.get("fake")
        assert r.retriever_name == "fake"

    def test_get_unknown(self):
        reg = RetrieverRegistry()
        with pytest.raises(RetrieverNotFoundError):
            reg.get("nonexistent")

    def test_lazy_instantiation(self):
        reg = RetrieverRegistry()
        reg.register("fake", _FakeRetriever)
        s1 = reg.get("fake")
        s2 = reg.get("fake")
        assert s1 is s2

    def test_unregister(self):
        reg = RetrieverRegistry()
        reg.register("fake", _FakeRetriever)
        reg.unregister("fake")
        assert "fake" not in reg.list_names()

    def test_double_register(self):
        reg = RetrieverRegistry()
        reg.register("fake", _FakeRetriever)
        with pytest.raises(ValueError):
            reg.register("fake", _FakeRetriever)


class TestRetrieverFactory:
    def test_create(self):
        factory = RetrieverFactory()
        factory.registry.register("fake", _FakeRetriever)
        r = factory.create("fake")
        assert isinstance(r, _FakeRetriever)

    def test_create_unknown(self):
        factory = RetrieverFactory()
        with pytest.raises(RetrieverNotFoundError):
            factory.create("unknown")

    def test_create_with_aliases(self):
        factory = RetrieverFactory()
        factory.registry.register("dense", _FakeRetriever)
        r = factory.create("default")
        assert isinstance(r, _FakeRetriever)

    def test_available_retrievers(self):
        factory = RetrieverFactory()
        factory.registry.register("a", _FakeRetriever)
        factory.registry.register("b", _FakeRetriever)
        stores = factory.available_retrievers()
        assert "a" in stores
        assert "b" in stores


class TestRetrieverConfiguration:
    def test_defaults(self):
        cfg = RetrieverConfiguration.default()
        assert cfg.retriever == "dense"
        assert cfg.top_k == 10

    def test_merge(self):
        cfg = RetrieverConfiguration.default()
        merged = cfg.merge({"top_k": 25})
        assert merged.top_k == 25
        assert cfg.top_k == 10

    def test_custom(self):
        cfg = RetrieverConfiguration(
            retriever="hybrid",
            top_k=20,
            weights={"dense": 0.7, "sparse": 0.3},
        )
        assert cfg.retriever == "hybrid"
        assert cfg.weights["dense"] == 0.7
