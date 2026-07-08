"""Tests for OllamaEmbeddingProvider."""

import pytest

from src.ai_core.embedding.providers.ollama import OllamaEmbeddingProvider


class TestOllamaEmbeddingProvider:
    def test_provider_name(self):
        provider = OllamaEmbeddingProvider()
        assert provider.provider_name == "ollama"

    def test_model_name(self):
        provider = OllamaEmbeddingProvider(model_name="nomic-embed-text")
        assert "nomic" in provider.model_name

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Health check returns bool, doesn't crash if Ollama not running."""
        provider = OllamaEmbeddingProvider()
        healthy = await provider.health_check()
        assert isinstance(healthy, bool)

    @pytest.mark.asyncio
    async def test_model_exists(self):
        provider = OllamaEmbeddingProvider()
        exists = await provider.model_exists()
        assert isinstance(exists, bool)

    @pytest.mark.asyncio
    async def test_embed_single(self):
        """Requires a running Ollama server with nomic-embed-text."""
        provider = OllamaEmbeddingProvider()
        if not await provider.health_check():
            pytest.skip("Ollama not available")
        vec = await provider.embed("Hello world")
        assert len(vec) > 0
        assert all(isinstance(v, float) for v in vec)

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """Requires a running Ollama server with nomic-embed-text."""
        provider = OllamaEmbeddingProvider()
        if not await provider.health_check():
            pytest.skip("Ollama not available")
        texts = ["First text", "Second text"]
        vectors = await provider.embed_batch(texts)
        assert len(vectors) == 2
        assert len(vectors[0]) > 0

    @pytest.mark.asyncio
    async def test_empty_batch(self):
        provider = OllamaEmbeddingProvider()
        vectors = await provider.embed_batch([])
        assert vectors == []

    @pytest.mark.asyncio
    async def test_dimensions_without_connection(self):
        """Should return default dimensions without making API call."""
        provider = OllamaEmbeddingProvider()
        # Accessing dimensions in async context should return the fallback
        # because the probe can't run synchronously
        dims = provider.dimensions
        assert dims == 768  # nomic-embed-text default

    @pytest.mark.asyncio
    async def test_configure(self):
        provider = OllamaEmbeddingProvider()
        provider.configure({"model_name": "test-model"})
        assert provider._model_name == "test-model"
