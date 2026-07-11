"""Tests for DenseRetriever."""

from unittest.mock import MagicMock

import pytest

from src.ai_core.embedding.base import EmbeddingProvider
from src.ai_core.retrieval.models import SearchQuery
from src.ai_core.retrieval.providers.dense import DenseRetriever


class _MockEmbedder(EmbeddingProvider):
    @property
    def dimensions(self) -> int:
        return 4

    @property
    def model_name(self) -> str:
        return "mock"

    @property
    def provider_name(self) -> str:
        return "mock"

    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3, 0.4]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    def configure(self, params: dict) -> None:
        pass


def _make_chroma_mock():
    """Return a mock ChromaDB collection.query result."""
    mock = MagicMock()
    mock.query.return_value = {
        "ids": [["c1", "c2"]],
        "distances": [[0.1, 0.3]],
        "documents": [["doc1 content", "doc2 content"]],
        "metadatas": [[{"report_id": "r1"}, {"report_id": "r2"}]],
    }
    return mock


class TestDenseRetriever:
    @pytest.fixture
    def retriever(self):
        embedder = _MockEmbedder()
        chroma = _make_chroma_mock()
        return DenseRetriever(
            embedding_provider=embedder,
            chroma_collection=chroma,
            top_k=5,
        )

    async def test_retrieve_basic(self, retriever):
        query = SearchQuery(text="test query", top_k=5)
        result = await retriever.retrieve(query)
        assert result.successful is True
        assert len(result.chunks) > 0
        assert result.chunks[0].chunk_id == "c1"

    async def test_empty_query(self, retriever):
        query = SearchQuery(text="")
        result = await retriever.retrieve(query)
        assert result.successful is False
        assert len(result.errors) > 0

    async def test_score_threshold(self, retriever):
        query = SearchQuery(text="test", top_k=5, score_threshold=0.9)
        result = await retriever.retrieve(query)
        assert result.successful is True
        for c in result.chunks:
            assert c.score >= 0.9

    async def test_no_embedding_provider(self):
        chroma = _make_chroma_mock()
        r = DenseRetriever(embedding_provider=None, chroma_collection=chroma)
        query = SearchQuery(text="test")
        result = await r.retrieve(query)
        assert result.successful is False
        assert any("Embedding" in e for e in result.errors)

    async def test_score_ordering(self, retriever):
        query = SearchQuery(text="test", top_k=5)
        result = await retriever.retrieve(query)
        scores = [c.score for c in result.chunks]
        assert scores == sorted(scores, reverse=True)

    async def test_configure(self):
        r = DenseRetriever()
        r.configure({"top_k": 20, "collection": "custom"})
        assert r._top_k == 20
        assert r._collection_name == "custom"

    async def test_retriever_name(self, retriever):
        assert retriever.retriever_name == "dense"
