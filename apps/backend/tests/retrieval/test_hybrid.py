"""Tests for HybridRetriever."""

from unittest.mock import MagicMock

import pytest

from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk, SearchQuery
from src.ai_core.retrieval.providers.hybrid import HybridRetriever


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
        assert r._weights["dense"] == 0.8
        assert r._weights["sparse"] == 0.5

    async def test_retriever_name(self, retriever):
        assert retriever.retriever_name == "hybrid"
