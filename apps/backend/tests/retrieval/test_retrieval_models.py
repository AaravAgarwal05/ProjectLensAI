"""Tests for retrieval models."""

from src.ai_core.retrieval.models import (
    RetrievalMetadata,
    RetrievalResult,
    RetrievalStatistics,
    RetrievedChunk,
    SearchQuery,
)


class TestSearchQuery:
    def test_defaults(self):
        q = SearchQuery(text="hello")
        assert q.text == "hello"
        assert q.top_k == 10
        assert q.score_threshold is None
        assert q.include_metadata is True

    def test_custom(self):
        q = SearchQuery(text="test", top_k=5, score_threshold=0.5, include_metadata=False)
        assert q.top_k == 5
        assert q.score_threshold == 0.5
        assert q.include_metadata is False


class TestRetrievedChunk:
    def test_minimal(self):
        c = RetrievedChunk(chunk_id="c1", content="hello", score=0.95)
        assert c.chunk_id == "c1"
        assert c.score == 0.95
        assert c.metadata == {}

    def test_with_metadata(self):
        c = RetrievedChunk(
            chunk_id="c1",
            content="data",
            score=0.8,
            metadata={"report_id": "r1"},
            document_id="d1",
        )
        assert c.document_id == "d1"
        assert c.metadata["report_id"] == "r1"


class TestRetrievalResult:
    def test_defaults(self):
        r = RetrievalResult()
        assert r.chunks == []
        assert r.successful is True
        assert r.warnings == []

    def test_with_chunks(self):
        chunks = [
            RetrievedChunk(chunk_id="c1", content="a", score=0.9),
            RetrievedChunk(chunk_id="c2", content="b", score=0.8),
        ]
        r = RetrievalResult(chunks=chunks, successful=True)
        assert len(r.chunks) == 2
        assert r.successful is True


class TestRetrievalMetadata:
    def test_defaults(self):
        m = RetrievalMetadata()
        assert m.query_text == ""
        assert m.retriever_name == ""
        assert m.total_time == 0.0


class TestRetrievalStatistics:
    def test_defaults(self):
        s = RetrievalStatistics()
        assert s.latency == 0.0
        assert s.recall == 0.0
        assert s.ndcg == 0.0
        assert s.num_queries == 0
