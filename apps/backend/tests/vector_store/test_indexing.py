"""Tests for IndexingEngine."""

import pytest

from src.ai_core.embedding.models import EmbeddedChunk, EmbeddingVector
from src.ai_core.vector_store.indexing import IndexingEngine
from src.ai_core.vector_store.providers.chroma_store import ChromaVectorStore


@pytest.fixture
def store():
    return ChromaVectorStore()


@pytest.fixture
def sample_chunks():
    return [
        EmbeddedChunk(
            chunk_id="c1",
            vector=EmbeddingVector(vector=[0.1, 0.2, 0.3, 0.4], dimensions=4),
            embedding_model="test",
            embedding_provider="test",
            dimensions=4,
        ),
        EmbeddedChunk(
            chunk_id="c2",
            vector=EmbeddingVector(vector=[0.5, 0.6, 0.7, 0.8], dimensions=4),
            embedding_model="test",
            embedding_provider="test",
            dimensions=4,
        ),
    ]


class TestIndexingEngine:
    async def test_index_empty(self):
        engine = IndexingEngine(store=ChromaVectorStore())
        result = await engine.index([])
        assert result.successful is True
        assert "No chunks provided" in result.warnings

    async def test_index(self, store, sample_chunks):
        engine = IndexingEngine(store=store)
        result = await engine.index(sample_chunks, collection="test_index")
        assert result.successful is True
        assert len(result.documents) == 2

    async def test_statistics(self, store, sample_chunks):
        engine = IndexingEngine(store=store)
        result = await engine.index(sample_chunks, collection="test_stats")
        assert result.statistics.total_documents == 2
        assert result.statistics.successful == 2
        assert result.statistics.total_time > 0
        assert result.statistics.throughput > 0

    async def test_delete(self, store, sample_chunks):
        engine = IndexingEngine(store=store)
        await engine.index(sample_chunks, collection="test_delete")
        result = await engine.delete(["c1"], collection="test_delete")
        assert result.collection_name == "test_delete"
        assert result.deleted_count == 1 or result.successful is True

    async def test_reindex(self, store, sample_chunks):
        engine = IndexingEngine(store=store)
        await engine.index(sample_chunks, collection="test_reindex")
        result = await engine.reindex(sample_chunks, collection="test_reindex")
        assert result.successful is True

    async def test_count(self, store, sample_chunks):
        engine = IndexingEngine(store=store)
        await engine.index(sample_chunks, collection="test_count")
        cnt = await engine.count(collection="test_count")
        assert cnt == 2

    async def test_delete_by_report(self, store, sample_chunks):
        engine = IndexingEngine(store=store)
        # Add report_id via extra metadata
        chunks = []
        for c in sample_chunks:
            c.metadata.extra["report_id"] = "r1"
            chunks.append(c)
        await engine.index(chunks, collection="test_del_report")
        result = await engine.delete_by_report("r1", collection="test_del_report")
        assert result.successful is True

    async def test_batch_indexing(self, store):
        """Test indexing with explicit batch_size."""
        chunks = [
            EmbeddedChunk(
                chunk_id=f"c{i}",
                vector=EmbeddingVector(vector=[0.1] * 4, dimensions=4),
                embedding_model="test",
                embedding_provider="test",
                dimensions=4,
            )
            for i in range(10)
        ]
        engine = IndexingEngine(store=store)
        result = await engine.index(chunks, collection="test_batch", batch_size=3)
        assert result.successful is True
        assert len(result.documents) == 10
