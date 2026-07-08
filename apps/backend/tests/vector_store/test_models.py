"""Tests for vector-store models."""

from src.ai_core.vector_store.models import (
    DeleteResult,
    IndexingResult,
    IndexingStatistics,
    UpdateResult,
    VectorDocument,
    VectorMetadata,
)


class TestVectorMetadata:
    def test_defaults(self):
        m = VectorMetadata(chunk_id="chunk_1")
        assert m.chunk_id == "chunk_1"
        assert m.report_id == ""
        assert m.version_id == ""
        assert m.embedding_model == ""
        assert m.extra == {}

    def test_all_fields(self):
        m = VectorMetadata(
            chunk_id="chunk_1",
            report_id="report_1",
            version_id="version_1",
            embedding_model="bge-small",
            embedding_provider="sentence_transformers",
            extra={"key": "value"},
        )
        assert m.report_id == "report_1"
        assert m.extra["key"] == "value"


class TestVectorDocument:
    def test_minimal(self):
        doc = VectorDocument(chunk_id="chunk_1", vector=[0.1, 0.2, 0.3])
        assert doc.chunk_id == "chunk_1"
        assert doc.vector == [0.1, 0.2, 0.3]
        assert doc.id == ""

    def test_with_metadata(self):
        meta = VectorMetadata(chunk_id="chunk_1", report_id="r1")
        doc = VectorDocument(chunk_id="chunk_1", vector=[0.1], dimensions=1, metadata=meta)
        assert doc.dimensions == 1
        assert doc.metadata.report_id == "r1"


class TestIndexingStatistics:
    def test_defaults(self):
        s = IndexingStatistics()
        assert s.total_documents == 0
        assert s.successful == 0
        assert s.failed == 0
        assert s.total_time == 0.0
        assert s.memory_usage is None


class TestIndexingResult:
    def test_defaults(self):
        r = IndexingResult()
        assert r.documents == []
        assert r.successful is True
        assert r.warnings == []

    def test_with_documents(self):
        docs = [
            VectorDocument(chunk_id="c1", vector=[0.1]),
            VectorDocument(chunk_id="c2", vector=[0.2]),
        ]
        r = IndexingResult(documents=docs, collection_name="test")
        assert len(r.documents) == 2
        assert r.collection_name == "test"


class TestDeleteResult:
    def test_success(self):
        r = DeleteResult(deleted_count=5, collection_name="col")
        assert r.deleted_count == 5
        assert r.successful is True

    def test_with_error(self):
        r = DeleteResult(collection_name="col", successful=False, errors=["not found"])
        assert r.successful is False
        assert len(r.errors) == 1


class TestUpdateResult:
    def test_success(self):
        r = UpdateResult(updated_count=3, collection_name="col")
        assert r.updated_count == 3
        assert r.successful is True
