"""Tests for EmbeddingPipeline."""

import pytest

from src.ai_core.chunking.models import Chunk
from src.ai_core.embedding.configuration import EmbeddingConfiguration
from src.ai_core.embedding.factory import EmbeddingFactory
from src.ai_core.embedding.pipeline import EmbeddingPipeline
from src.ai_core.embedding.registry import EmbeddingRegistry
from src.ai_core.embedding.validation import EmbeddingValidationEngine


class _MockProvider:
    """Mock provider that returns deterministic vectors."""

    provider_name = "mock"
    _model_name = "mock-model"

    @property
    def dimensions(self):
        return 3

    @property
    def model_name(self):
        return self._model_name

    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def configure(self, params: dict) -> None:
        if "model_name" in params:
            self._model_name = params["model_name"]

    async def health_check(self) -> bool:
        return True


class _FailingProvider(_MockProvider):
    """Provider that fails on batch embedding."""

    provider_name = "fail"

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("Batch failed")


def _make_factory() -> EmbeddingFactory:
    reg = EmbeddingRegistry()
    reg.register("mock", _MockProvider)
    reg.register("fail", _FailingProvider)
    return EmbeddingFactory(reg)


class TestEmbeddingPipeline:
    @pytest.mark.asyncio
    async def test_run(self):
        factory = _make_factory()
        pipeline = EmbeddingPipeline(factory)
        chunks = [Chunk(text="Hello")]
        result = await pipeline.run(chunks, provider="mock")
        assert result.successful is True
        assert len(result.embeddings) == 1
        assert result.embeddings[0].vector.vector == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_run_multiple_chunks(self):
        factory = _make_factory()
        pipeline = EmbeddingPipeline(factory)
        chunks = [Chunk(text=f"Chunk {i}") for i in range(5)]
        result = await pipeline.run(chunks, provider="mock")
        assert result.successful is True
        assert len(result.embeddings) == 5

    @pytest.mark.asyncio
    async def test_batching(self):
        factory = _make_factory()
        cfg = EmbeddingConfiguration(batch_size=2)
        pipeline = EmbeddingPipeline(factory, config=cfg)
        chunks = [Chunk(text=f"Chunk {i}") for i in range(7)]
        result = await pipeline.run(chunks, provider="mock")
        assert len(result.embeddings) == 7
        assert result.statistics.total_batches >= 4

    @pytest.mark.asyncio
    async def test_empty_chunks(self):
        factory = _make_factory()
        pipeline = EmbeddingPipeline(factory)
        result = await pipeline.run([], provider="mock")
        assert result.successful is True
        assert result.embeddings == []

    @pytest.mark.asyncio
    async def test_unknown_provider(self):
        factory = _make_factory()
        pipeline = EmbeddingPipeline(factory)
        result = await pipeline.run([Chunk(text="h")], provider="unknown")
        assert result.successful is False

    @pytest.mark.asyncio
    async def test_with_validation(self):
        engine = EmbeddingValidationEngine()
        factory = _make_factory()
        pipeline = EmbeddingPipeline(factory, validation=engine)
        chunks = [Chunk(text="test")]
        result = await pipeline.run(chunks, provider="mock")
        assert result.successful is True

    @pytest.mark.asyncio
    async def test_batch_error_handling(self):
        factory = _make_factory()
        pipeline = EmbeddingPipeline(factory)
        chunks = [Chunk(text="test")]
        result = await pipeline.run(chunks, provider="fail")
        # Even with failures, pipeline should produce results
        assert len(result.embeddings) == 1

    @pytest.mark.asyncio
    async def test_statistics_populated(self):
        factory = _make_factory()
        pipeline = EmbeddingPipeline(factory)
        chunks = [Chunk(text=f"Chunk {i}") for i in range(10)]
        result = await pipeline.run(chunks, provider="mock")
        assert result.statistics.total_chunks == 10
        assert result.statistics.total_processing_time > 0
        assert result.statistics.dimensions == 3
        assert result.statistics.model_name == "mock-model"
        assert result.statistics.provider_name == "mock"
