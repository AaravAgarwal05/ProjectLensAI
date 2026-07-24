"""Tests for embedding models."""

from src.ai_core.embedding.models import (
    EmbeddedChunk,
    EmbeddingMetadata,
    EmbeddingResult,
    EmbeddingStatistics,
    EmbeddingVector,
)


class TestEmbeddingVector:
    def test_defaults(self):
        vec = EmbeddingVector(vector=[0.1, 0.2, 0.3], dimensions=3)
        assert len(vec.vector) == 3
        assert vec.dimensions == 3

    def test_from_list(self):
        vec = EmbeddingVector.from_list([0.1, 0.2, 0.3])
        assert vec.dimensions == 3

    def test_empty_vector(self):
        vec = EmbeddingVector(vector=[], dimensions=0)
        assert vec.dimensions == 0


class TestEmbeddingMetadata:
    def test_defaults(self):
        meta = EmbeddingMetadata()
        assert meta.provider == "unknown"
        assert meta.model == "unknown"
        assert meta.extra == {}

    def test_all_fields(self):
        meta = EmbeddingMetadata(
            provider="test",
            model="test-model",
            batch_index=0,
            chunk_text_length=100,
        )
        assert meta.provider == "test"
        assert meta.model == "test-model"
        assert meta.batch_index == 0


class TestEmbeddedChunk:
    def test_minimal(self):
        vec = EmbeddingVector(vector=[0.1], dimensions=1)
        chunk = EmbeddedChunk(
            chunk_id="abc-123",
            vector=vec,
            embedding_model="bge",
            embedding_provider="st",
            dimensions=1,
        )
        assert chunk.chunk_id == "abc-123"
        assert chunk.vector.vector == [0.1]
        assert chunk.embedding_model == "bge"
        assert chunk.metadata.provider == "unknown"

    def test_with_metadata(self):
        meta = EmbeddingMetadata(provider="ollama", model="nomic")
        vec = EmbeddingVector(vector=[0.5], dimensions=1)
        chunk = EmbeddedChunk(
            chunk_id="xyz",
            vector=vec,
            embedding_model="nomic",
            embedding_provider="ollama",
            dimensions=1,
            metadata=meta,
        )
        assert chunk.metadata.provider == "ollama"
        assert chunk.created_at is not None


class TestEmbeddingStatistics:
    def test_defaults(self):
        stats = EmbeddingStatistics()
        assert stats.total_chunks == 0
        assert stats.total_processing_time == 0.0
        assert stats.throughput == 0.0

    def test_round_trip(self):
        stats = EmbeddingStatistics(
            total_chunks=100,
            total_batches=4,
            average_batch_size=25.0,
            total_processing_time=2.5,
            embedding_latency=0.625,
            throughput=40.0,
            dimensions=384,
            model_name="bge",
            provider_name="st",
            memory_usage=1024,
        )
        assert stats.total_chunks == 100
        assert stats.throughput == 40.0
        assert stats.dimensions == 384
        assert stats.provider_name == "st"


class TestEmbeddingResult:
    def test_defaults(self):
        result = EmbeddingResult()
        assert result.embeddings == []
        assert result.warnings == []
        assert result.successful is True

    def test_with_embeddings(self):
        vec = EmbeddingVector(vector=[0.1], dimensions=1)
        e1 = EmbeddedChunk(
            chunk_id="1", vector=vec, embedding_model="m", embedding_provider="p", dimensions=1
        )
        e2 = EmbeddedChunk(
            chunk_id="2",
            vector=EmbeddingVector(vector=[0.2], dimensions=1),
            embedding_model="m",
            embedding_provider="p",
            dimensions=1,
        )
        result = EmbeddingResult(embeddings=[e1, e2])
        assert len(result.embeddings) == 2
        assert result.successful is True

    def test_not_successful(self):
        result = EmbeddingResult(errors=["provider failed"], successful=False)
        assert result.successful is False
