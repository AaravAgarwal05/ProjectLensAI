"""Tests for ChromaVectorStore provider."""

import pytest

from src.ai_core.vector_store.models import VectorDocument, VectorMetadata
from src.ai_core.vector_store.providers.chroma_store import ChromaVectorStore


@pytest.fixture
def store():
    return ChromaVectorStore()


@pytest.fixture
def sample_docs():
    return [
        VectorDocument(
            chunk_id="c1",
            vector=[0.1, 0.2, 0.3, 0.4],
            dimensions=4,
            metadata=VectorMetadata(
                chunk_id="c1",
                report_id="r1",
                version_id="v1",
                embedding_model="test",
                embedding_provider="test",
            ),
        ),
        VectorDocument(
            chunk_id="c2",
            vector=[0.5, 0.6, 0.7, 0.8],
            dimensions=4,
            metadata=VectorMetadata(
                chunk_id="c2",
                report_id="r1",
                version_id="v2",
                embedding_model="test",
                embedding_provider="test",
            ),
        ),
    ]


class TestChromaVectorStore:
    async def test_health_check(self, store):
        assert await store.health_check() is True

    async def test_create_collection(self, store):
        result = await store.create_collection("test_col", dimensions=4)
        assert result is True

    async def test_create_collection_duplicate(self, store):
        await store.create_collection("dup_test", dimensions=4)
        result = await store.create_collection("dup_test", dimensions=4)
        assert result is False

    async def test_collection_exists(self, store):
        await store.create_collection("exists_test", dimensions=4)
        assert await store.collection_exists("exists_test") is True
        assert await store.collection_exists("nonexistent") is False

    async def test_insert(self, store, sample_docs):
        await store.create_collection("insert_test", dimensions=4)
        count = await store.insert("insert_test", sample_docs)
        assert count == 2

    async def test_count(self, store, sample_docs):
        await store.create_collection("count_test", dimensions=4)
        await store.insert("count_test", sample_docs)
        assert await store.count("count_test") == 2

    async def test_delete_by_chunk_ids(self, store, sample_docs):
        await store.create_collection("delete_test", dimensions=4)
        await store.insert("delete_test", sample_docs)
        deleted = await store.delete("delete_test", chunk_ids=["c1"])
        assert deleted == 1
        assert await store.count("delete_test") == 1

    async def test_update(self, store, sample_docs):
        await store.create_collection("update_test", dimensions=4)
        await store.insert("update_test", sample_docs)
        updated = sample_docs[0]
        updated.vector = [0.9, 0.9, 0.9, 0.9]
        count = await store.update("update_test", [updated])
        assert count == 1

    async def test_delete_by_report(self, store, sample_docs):
        await store.create_collection("report_test", dimensions=4)
        await store.insert("report_test", sample_docs)
        result = await store.delete_by_report("report_test", "r1")
        assert result.successful is True

    async def test_delete_by_version(self, store, sample_docs):
        await store.create_collection("version_test", dimensions=4)
        await store.insert("version_test", sample_docs)
        result = await store.delete_by_version("version_test", "v1")
        assert result.successful is True

    async def test_configure(self):
        s = ChromaVectorStore(path="/tmp/test_chroma")
        s.configure({"path": "/tmp/test_chroma_2"})
        # Path changed, client will be lazy-recreated
        assert s._path == "/tmp/test_chroma_2"
