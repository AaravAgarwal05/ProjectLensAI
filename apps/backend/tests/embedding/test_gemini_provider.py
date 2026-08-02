"""Tests for GeminiEmbeddingProvider (HTTP layer mocked)."""

import httpx
import pytest

from src.ai_core.embedding.providers.gemini import GeminiEmbeddingProvider


def _provider(handler) -> GeminiEmbeddingProvider:
    """Provider wired to a mock transport so no network is touched."""
    provider = GeminiEmbeddingProvider(api_key="test-key")
    provider._client = httpx.AsyncClient(
        base_url="https://generativelanguage.googleapis.com/v1beta",
        transport=httpx.MockTransport(handler),
    )
    return provider


def _ok_handler(request: httpx.Request) -> httpx.Response:
    if ":batchEmbedContents" in str(request.url):
        return httpx.Response(
            200,
            json={
                "embeddings": [
                    {"values": [0.1, 0.2, 0.3]},
                    {"values": [0.4, 0.5, 0.6]},
                ]
            },
        )
    return httpx.Response(200, json={"embedding": {"values": [0.1, 0.2, 0.3]}})


class TestGeminiEmbeddingProvider:
    def test_provider_name(self):
        assert GeminiEmbeddingProvider().provider_name == "gemini"

    def test_model_name_default(self):
        assert GeminiEmbeddingProvider().model_name == "text-embedding-004"

    def test_dimensions_default(self):
        assert GeminiEmbeddingProvider().dimensions == 768

    @pytest.mark.asyncio
    async def test_embed_single(self):
        provider = _provider(_ok_handler)
        vector = await provider.embed("Hello world")
        assert len(vector) == 3
        assert all(isinstance(v, float) for v in vector)
        # L2-normalized → unit length
        norm = sum(v * v for v in vector) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        provider = _provider(_ok_handler)
        vectors = await provider.embed_batch(["First", "Second"])
        assert len(vectors) == 2
        assert all(len(v) == 3 for v in vectors)

    @pytest.mark.asyncio
    async def test_empty_batch(self):
        provider = _provider(_ok_handler)
        assert await provider.embed_batch([]) == []

    @pytest.mark.asyncio
    async def test_embed_dimension_updates_from_response(self):
        provider = _provider(_ok_handler)
        await provider.embed("x")
        assert provider.dimensions == 3

    @pytest.mark.asyncio
    async def test_embed_raises_on_api_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": {"message": "quota exceeded"}})

        provider = _provider(handler)
        with pytest.raises(RuntimeError, match="quota exceeded"):
            await provider.embed("x")

    @pytest.mark.asyncio
    async def test_health_check(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        provider = _provider(handler)
        assert await provider.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_false_on_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={})

        provider = _provider(handler)
        assert await provider.health_check() is False

    def test_configure_resets_dimensions(self):
        provider = _provider(_ok_handler)
        provider.configure({"model_name": "gemini-embedding-001"})
        assert provider.model_name == "gemini-embedding-001"
        assert provider.dimensions == 768
