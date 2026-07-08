"""Tests for SentenceTransformerProvider."""

import pytest

from src.ai_core.embedding.providers.sentence_transformer import SentenceTransformerProvider


class TestSentenceTransformerProvider:
    def test_provider_name(self):
        provider = SentenceTransformerProvider()
        assert provider.provider_name == "sentence_transformers"

    def test_model_name(self):
        provider = SentenceTransformerProvider()
        assert "bge" in provider.model_name.lower()

    @pytest.mark.asyncio
    async def test_embed_single(self):
        provider = SentenceTransformerProvider()
        vec = await provider.embed("Hello world")
        assert len(vec) > 0
        assert all(isinstance(v, float) for v in vec)

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        provider = SentenceTransformerProvider(batch_size=2)
        texts = ["Hello world", "Second text", "Third text here"]
        vectors = await provider.embed_batch(texts)
        assert len(vectors) == 3
        assert all(len(v) > 0 for v in vectors)
        assert len(vectors[0]) == provider.dimensions

    @pytest.mark.asyncio
    async def test_dimensions(self):
        provider = SentenceTransformerProvider()
        dims = provider.dimensions
        assert dims > 0
        # bge-small-en-v1.5 is 384-dim
        assert dims == 384

    @pytest.mark.asyncio
    async def test_empty_batch(self):
        provider = SentenceTransformerProvider()
        vectors = await provider.embed_batch([])
        assert vectors == []

    @pytest.mark.asyncio
    async def test_configure(self):
        provider = SentenceTransformerProvider()
        provider.configure({"batch_size": 64})
        assert provider._batch_size == 64

    @pytest.mark.asyncio
    async def test_normalize(self):
        provider = SentenceTransformerProvider(normalize_embeddings=True)
        vec = await provider.embed("Test")
        magnitude = sum(v * v for v in vec) ** 0.5
        assert abs(magnitude - 1.0) < 0.01  # L2 normalized

    @pytest.mark.asyncio
    async def test_model_name_property(self):
        provider = SentenceTransformerProvider(model_name="BAAI/bge-small-en-v1.5")
        assert provider.model_name == "BAAI/bge-small-en-v1.5"
