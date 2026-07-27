"""Tests for HybridRetriever."""

from unittest.mock import MagicMock

import pytest

from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk, SearchQuery
from src.ai_core.retrieval.providers.hybrid import HybridRetriever, _BM25Okapi


class _MockDense:
    @property
    def retriever_name(self) -> str:
        return "dense"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        return RetrievalResult(
            chunks=[
                RetrievedChunk(chunk_id="c1", content="dense result 1", score=0.9),
                RetrievedChunk(chunk_id="c2", content="dense result 2", score=0.7),
            ],
            successful=True,
        )

    def configure(self, params: dict) -> None:
        pass


def _make_chroma_mock():
    mock = MagicMock()
    mock.get.return_value = {
        "ids": ["c1", "c2", "c3"],
        "documents": ["dense result 1", "dense result 2", "sparse content"],
        "metadatas": [{"report_id": "r1"}, {"report_id": "r1"}, {"report_id": "r2"}],
    }
    return mock


class TestHybridRetriever:
    @pytest.fixture
    def retriever(self):
        dense = _MockDense()
        chroma = _make_chroma_mock()
        return HybridRetriever(
            dense_retriever=dense,
            chroma_collection=chroma,
            weights={"dense": 0.6, "sparse": 0.4},
            top_k=5,
        )

    async def test_retrieve_basic(self, retriever):
        query = SearchQuery(text="test query", top_k=5)
        result = await retriever.retrieve(query)
        assert result.successful is True
        assert len(result.chunks) > 0

    async def test_empty_query(self, retriever):
        query = SearchQuery(text="")
        result = await retriever.retrieve(query)
        assert result.successful is False

    async def test_chunks_have_scores(self, retriever):
        query = SearchQuery(text="find something", top_k=5)
        result = await retriever.retrieve(query)
        for c in result.chunks:
            assert c.score > 0

    async def test_score_ordering(self, retriever):
        query = SearchQuery(text="test", top_k=5)
        result = await retriever.retrieve(query)
        scores = [c.score for c in result.chunks]
        assert scores == sorted(scores, reverse=True)

    async def test_weight_configuration(self):
        r = HybridRetriever()
        r.configure({"weights": {"dense": 0.8}})
        total = sum(r._weights.values())
        assert abs(total - 1.0) < 1e-6, f"Weights should sum to 1.0, got {total}"
        assert r._weights["dense"] == 0.8 / 1.3
        assert r._weights["sparse"] == 0.5 / 1.3

    async def test_retriever_name(self, retriever):
        assert retriever.retriever_name == "hybrid"


class TestBM25Okapi:
    def test_build_and_score(self):
        bm25 = _BM25Okapi()
        docs = [
            "the cat sat on the mat",
            "the dog chased the cat",
            "the bird flew over the mat",
        ]
        bm25.build(docs)
        scores = bm25.score_all("cat mat")
        assert len(scores) == 3
        # First doc (cat + mat) should score higher for "cat mat"
        assert scores[0] > scores[1]
        assert all(s >= 0 for s in scores)

    def test_empty_corpus(self):
        bm25 = _BM25Okapi()
        bm25.build([])
        assert bm25.score_all("test") == []

    def test_score_out_of_range(self):
        bm25 = _BM25Okapi()
        assert bm25.score("hello", 0) == 0.0  # no build yet
        bm25.build(["hello world"])
        bad_idx = bm25.score("hello", 999)
        assert bad_idx == 0.0

    def test_zero_query(self):
        bm25 = _BM25Okapi()
        bm25.build(["hello world"])
        scores = bm25.score_all("")
        assert all(s == 0.0 for s in scores)

    def test_params_impact(self):
        docs = ["a a a a a a a a a a", "b b", "a a a"]  # varied lengths
        bm25_high_b = _BM25Okapi(k1=1.2, b=1.0)
        bm25_low_b = _BM25Okapi(k1=1.2, b=0.0)
        bm25_high_b.build(docs)
        bm25_low_b.build(docs)
        # b=1.0 penalises longer docs, b=0.0 doesn't
        scores_high = bm25_high_b.score_all("a")
        scores_low = bm25_low_b.score_all("a")
        assert scores_high != scores_low
