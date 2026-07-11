"""Tests for MultiQueryRetriever."""

import pytest

from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk, SearchQuery
from src.ai_core.retrieval.providers.multi_query import MultiQueryRetriever


class _MockBase:
    def __init__(self, chunks=None):
        self._chunks = chunks or [
            RetrievedChunk(chunk_id="c1", content="result 1", score=0.9),
            RetrievedChunk(chunk_id="c2", content="result 2", score=0.7),
        ]

    @property
    def retriever_name(self) -> str:
        return "dense"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        return RetrievalResult(chunks=self._chunks, successful=True)

    def configure(self, params: dict) -> None:
        pass


class TestMultiQueryRetriever:
    @pytest.fixture
    def retriever(self):
        return MultiQueryRetriever(
            base_retriever=_MockBase(),
            top_k=5,
            num_variants=3,
        )

    @pytest.fixture
    def retriever_one(self):
        return MultiQueryRetriever(
            base_retriever=_MockBase(),
            num_variants=1,
        )

    async def test_retrieve_basic(self, retriever):
        query = SearchQuery(text="find the document", top_k=5)
        result = await retriever.retrieve(query)
        assert result.successful is True
        assert len(result.chunks) > 0

    async def test_empty_query(self, retriever):
        query = SearchQuery(text="")
        result = await retriever.retrieve(query)
        assert result.successful is False

    async def test_deduplication(self, retriever):
        query = SearchQuery(text="test query please", top_k=5)
        result = await retriever.retrieve(query)
        chunk_ids = [c.chunk_id for c in result.chunks]
        assert len(chunk_ids) == len(set(chunk_ids))

    async def test_single_variant(self, retriever_one):
        query = SearchQuery(text="test", top_k=5)
        result = await retriever_one.retrieve(query)
        assert result.successful is True

    async def test_query_expansion(self, retriever):
        variants = retriever._expand_query("find the document please")
        assert len(variants) >= 1

    async def test_query_expansion_short(self, retriever):
        variants = retriever._expand_query("hello")
        assert len(variants) == 0

    async def test_retriever_name(self, retriever):
        assert retriever.retriever_name == "multi_query"

    async def test_configure(self):
        r = MultiQueryRetriever()
        r.configure({"top_k": 15, "num_variants": 5})
        assert r._top_k == 15
        assert r._num_variants == 5
