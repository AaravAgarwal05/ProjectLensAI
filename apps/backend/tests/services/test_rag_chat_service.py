"""Tests for RAGChatService — mocked ChromaDB, LLM, and embedding."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai_core.llm.models import LLMResponse
from src.services.rag_chat_service import RAGChatService

# ── helpers ──────────────────────────────────────────────────────────────────


def _make_chroma_query_result(
    ids: list[str] | None = None,
    distances: list[float] | None = None,
    documents: list[str] | None = None,
    metadatas: list[dict] | None = None,
) -> dict:
    return {
        "ids": [ids or ["c1", "c2"]],
        "distances": [distances or [0.1, 0.3]],
        "documents": [documents or ["doc1 content", "doc2 content"]],
        "metadatas": [metadatas or [{"report_id": "r1"}, {"report_id": "r1"}]],
    }


def _make_chroma_collection_mock(query_result: dict | None = None):
    col = MagicMock()
    col.query.return_value = query_result or _make_chroma_query_result()
    return col


def _patched_service(embedder=None, llm=None, collections=None):
    """Context manager: yields a RAGChatService with patched deps.

    Usage::

        async with _patched_service(collections={"report_r1": col}) as svc:
            await svc.answer("q", ["r1"])
    """
    if embedder is None:
        embedder = AsyncMock()
        embedder.provider_name = "ollama"
        embedder.embed.return_value = [0.1, 0.2, 0.3]
    if llm is None:
        llm = AsyncMock()
        llm.generate.return_value = LLMResponse(text="Answer.")

    chroma_client = MagicMock()
    chroma_client.get_collection.side_effect = (
        lambda name, cols=collections or {}: cols.get(name)
    )

    class _Ctx:
        async def __aenter__(self):
            self._p1 = patch("src.services.rag_chat_service.build_embedding_provider", return_value=embedder)
            self._p2 = patch("src.services.rag_chat_service.build_llm_provider", return_value=llm)
            self._p4 = patch.object(
                RAGChatService,
                "_get_chroma_client",
                new=AsyncMock(return_value=chroma_client),
            )
            self._p1.start()
            self._p2.start()
            self._p4.start()
            self.service = RAGChatService(top_k=5)
            return self.service

        async def __aexit__(self, *exc):
            self._p1.stop()
            self._p2.stop()
            self._p4.stop()

    return _Ctx()


# ── Tests ────────────────────────────────────────────────────────────────────


class TestRAGChatServiceAnswer:
    """Main answer flow."""

    async def test_answer_basic(self):
        """Happy path: embed → retrieve → generate → citations."""
        embedder = AsyncMock()
        embedder.provider_name = "ollama"
        embedder.embed.return_value = [0.1, 0.2, 0.3]

        llm = AsyncMock()
        llm.generate.return_value = LLMResponse(text="Based on excerpt [1], the answer is X.")

        col = _make_chroma_collection_mock()

        async with _patched_service(embedder=embedder, llm=llm, collections={"report_r1": col}) as svc:
            text, citations = await svc.answer("what is X?", ["r1"])

        assert "X" in text
        assert len(citations) == 2
        assert citations[0]["report_id"] == "r1"
        assert citations[0]["chunk_id"] == "c1"
        assert citations[0]["score"] == pytest.approx(1.0 / 1.1)  # 1/(1 + 0.1) = 0.909

    async def test_answer_no_chunks(self):
        """When no chunks retrieved, return fallback message."""
        embedder = AsyncMock()
        embedder.provider_name = "mock"
        embedder.embed.return_value = [0.1, 0.2, 0.3]

        async with _patched_service(embedder=embedder, collections={}) as svc:
            text, citations = await svc.answer("anything?", ["r1"])

        assert "couldn't find any relevant content" in text
        assert citations == []

    async def test_answer_multiple_reports(self):
        """Chunks from multiple reports are merged and sorted by score."""
        embedder = AsyncMock()
        embedder.provider_name = "ollama"
        embedder.embed.return_value = [0.1, 0.2, 0.3]

        llm = AsyncMock()
        llm.generate.return_value = LLMResponse(text="Answer.")

        col1 = _make_chroma_collection_mock(_make_chroma_query_result(
            ids=["c1"], distances=[0.1], documents=["doc1"], metadatas=[{"report_id": "r1"}],
        ))
        col2 = _make_chroma_collection_mock(_make_chroma_query_result(
            ids=["c2"], distances=[0.5], documents=["doc2"], metadatas=[{"report_id": "r2"}],
        ))

        async with _patched_service(
            embedder=embedder,
            llm=llm,
            collections={"report_r1": col1, "report_r2": col2},
        ) as svc:
            text, citations = await svc.answer("query", ["r1", "r2"])

        assert len(citations) == 2
        assert citations[0]["chunk_id"] == "c1"
        assert citations[0]["score"] >= citations[1]["score"]


class TestRAGChatServiceEmbedWithCache:
    """Embedding cache behaviour."""

    async def test_cache_hit(self):
        """Redis cache returns cached vector."""
        embedder = AsyncMock()
        embedder.provider_name = "ollama"
        embedder.embed.return_value = [9.9, 9.9]

        redis_client = AsyncMock()
        redis_client.get.return_value = "[1.0, 2.0, 3.0]"
        get_redis_mock = AsyncMock(return_value=redis_client)

        with patch("src.infra.redis.get_redis", new=get_redis_mock):
            async with _patched_service(embedder=embedder, collections={}) as svc:
                vector = await svc._embed_with_cache("hello")

        assert vector == [1.0, 2.0, 3.0]
        embedder.embed.assert_not_called()

    async def test_cache_miss_then_store(self):
        """Cache miss → embed → store in Redis."""
        embedder = AsyncMock()
        embedder.provider_name = "ollama"
        embedder.embed.return_value = [4.0, 5.0]

        redis_client = AsyncMock()
        redis_client.get.return_value = None
        get_redis_mock = AsyncMock(return_value=redis_client)

        stored: dict = {}
        set_json_mock = AsyncMock(side_effect=lambda k, v, expire=3600: stored.update({k: v}))

        with (
            patch("src.infra.redis.get_redis", new=get_redis_mock),
            patch("src.infra.redis.set_json", new=set_json_mock),
        ):
            async with _patched_service(embedder=embedder, collections={}) as svc:
                vector = await svc._embed_with_cache("hello")

        assert vector == [4.0, 5.0]
        embedder.embed.assert_awaited_once_with("hello")
        assert len(stored) == 1

    async def test_redis_unavailable_fallback(self):
        """When Redis is down, embed fresh and skip cache."""
        embedder = AsyncMock()
        embedder.provider_name = "ollama"
        embedder.embed.return_value = [7.0, 8.0]

        with patch("src.infra.redis.get_redis", side_effect=ConnectionError("Redis down")):
            async with _patched_service(embedder=embedder, collections={}) as svc:
                vector = await svc._embed_with_cache("hello")

        assert vector == [7.0, 8.0]

    async def test_cache_skipped_for_non_ollama(self):
        """Non-Ollama embedder bypasses Redis cache entirely."""
        embedder = AsyncMock()
        embedder.provider_name = "sentence_transformer"
        embedder.embed.return_value = [0.0, 1.0]

        async with _patched_service(embedder=embedder, collections={}) as svc:
            vector = await svc._embed_with_cache("hello")

        assert vector == [0.0, 1.0]
        embedder.embed.assert_awaited_once_with("hello")


class TestRAGChatServiceHelpers:

    def test_format_context(self):
        chunks = [
            {"content": "first chunk", "score": 0.9, "report_id": "r1"},
            {"content": "second chunk", "score": 0.5, "report_id": "r1"},
        ]
        service = RAGChatService(top_k=5)
        ctx = service._format_context(chunks)
        assert "[1]" in ctx
        assert "[2]" in ctx
        assert "first chunk" in ctx
        assert "second chunk" in ctx
        assert "0.90" in ctx
        assert "0.50" in ctx

    def test_format_context_respects_top_k(self):
        chunks = [
            {"content": f"chunk{i}", "score": 1.0 - i * 0.1, "report_id": "r1"}
            for i in range(20)
        ]
        service = RAGChatService(top_k=3)
        ctx = service._format_context(chunks)
        assert "[1]" in ctx
        assert "[2]" in ctx
        assert "[3]" in ctx
        assert "[4]" not in ctx

    async def test_trace_id_generated(self):
        tid1 = RAGChatService._make_trace_id()
        tid2 = RAGChatService._make_trace_id()
        assert len(tid1) == 12
        assert tid1 != tid2

    async def test_retrieve_chunks_empty_report_ids(self):
        embedder = AsyncMock()
        embedder.provider_name = "ollama"
        embedder.embed.return_value = [0.1, 0.2]

        async with _patched_service(embedder=embedder) as svc:
            chunks = await svc._retrieve_chunks("test", [])

        assert chunks == []

    async def test_answer_with_trace_id(self):
        """trace_id is passed through and logged."""
        embedder = AsyncMock()
        embedder.provider_name = "ollama"
        embedder.embed.return_value = [0.1, 0.2, 0.3]

        llm = AsyncMock()
        llm.generate.return_value = LLMResponse(text="ok")

        col = _make_chroma_collection_mock()

        async with _patched_service(embedder=embedder, llm=llm, collections={"report_r1": col}) as svc:
            text, citations = await svc.answer("hi", ["r1"], trace_id="test-trace-123")

        assert text == "ok"
        assert len(citations) > 0
