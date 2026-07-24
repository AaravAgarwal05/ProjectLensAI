"""Tests for embedding registry and factory."""

import pytest

from src.ai_core.embedding.exceptions import ProviderNotFoundError
from src.ai_core.embedding.factory import EmbeddingFactory
from src.ai_core.embedding.registry import EmbeddingRegistry


class _FakeProvider:
    """Minimal fake provider for registry testing."""

    provider_name = "fake"

    @property
    def dimensions(self):
        return 3

    @property
    def model_name(self):
        return "fake"

    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def configure(self, params: dict) -> None:
        pass


class TestEmbeddingRegistry:
    def test_register_and_get(self):
        reg = EmbeddingRegistry()
        reg.register("fake", _FakeProvider)
        provider = reg.get("fake")
        assert provider.provider_name == "fake"

    def test_get_unknown(self):
        reg = EmbeddingRegistry()
        with pytest.raises(ProviderNotFoundError):
            reg.get("nonexistent")

    def test_lazy_instantiation(self):
        reg = EmbeddingRegistry()
        reg.register("fake", _FakeProvider)
        p1 = reg.get("fake")
        p2 = reg.get("fake")
        assert p1 is p2

    def test_unregister(self):
        reg = EmbeddingRegistry()
        reg.register("fake", _FakeProvider)
        reg.unregister("fake")
        assert "fake" not in reg.list_names()

    def test_double_register(self):
        reg = EmbeddingRegistry()
        reg.register("fake", _FakeProvider)
        with pytest.raises(ValueError, match="already registered"):
            reg.register("fake", _FakeProvider)

    def test_create_all(self):
        reg = EmbeddingRegistry()
        reg.register("fake1", _FakeProvider)
        reg.register("fake2", _FakeProvider)
        providers = reg.create_all()
        assert len(providers) == 2


class TestEmbeddingFactory:
    def test_create(self):
        factory = EmbeddingFactory()
        factory.registry.register("fake", _FakeProvider)
        provider = factory.create("fake")
        assert isinstance(provider, _FakeProvider)

    def test_create_unknown(self):
        factory = EmbeddingFactory()
        with pytest.raises(ProviderNotFoundError):
            factory.create("unknown")

    def test_create_with_aliases(self):
        factory = EmbeddingFactory()
        factory.registry.register("sentence_transformers", _FakeProvider)
        provider = factory.create("st")
        assert isinstance(provider, _FakeProvider)

    def test_create_case_insensitive(self):
        factory = EmbeddingFactory()
        factory.registry.register("fake", _FakeProvider)
        provider = factory.create("FAKE")
        assert isinstance(provider, _FakeProvider)
