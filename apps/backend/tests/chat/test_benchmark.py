"""Tests for ChatBenchmark."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ai_core.chat.benchmark import ChatBenchmark
from src.ai_core.chat.models import ChatMessage, CitationReference


class TestChatBenchmark:
    @pytest.mark.asyncio
    async def test_run_basic(self):
        """Test benchmark run with mocked orchestrator."""
        orchestrator = MagicMock()
        orchestrator.process_message = AsyncMock(
            return_value=(
                ChatMessage(
                    id="m1",
                    session_id="s1",
                    role="assistant",
                    content="Test response with several words here",
                ),
                [
                    CitationReference(report_id="r1", chunk_id="c1", score=0.95),
                ],
            )
        )

        benchmark = ChatBenchmark(orchestrator)
        result = await benchmark.run(
            session_id="s1",
            messages=["Hello", "How are you?"],
            retrieve_chunks=None,
        )

        assert result.iterations == 2
        assert result.message_latency_avg > 0
        assert result.citations_per_response_avg == 1.0
        assert result.tokens_per_response_avg == 6  # 6 words in response
        assert result.conversation_length_avg == 2
        assert len(result.individual) == 2

    @pytest.mark.asyncio
    async def test_run_with_retrieval(self):
        """Test benchmark with retrieval callable."""
        orchestrator = MagicMock()
        orchestrator.process_message = AsyncMock(
            return_value=(
                ChatMessage(
                    id="m1",
                    session_id="s1",
                    role="assistant",
                    content="Response.",
                ),
                [],
            )
        )

        retrieve_chunks = MagicMock(return_value=["chunk1", "chunk2"])

        benchmark = ChatBenchmark(orchestrator)
        result = await benchmark.run(
            session_id="s1",
            messages=["Test"],
            retrieve_chunks=retrieve_chunks,
        )

        assert result.iterations == 1
        retrieve_chunks.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_empty_messages(self):
        """Test benchmark with no messages."""
        orchestrator = MagicMock()
        benchmark = ChatBenchmark(orchestrator)
        result = await benchmark.run(
            session_id="s1",
            messages=[],
        )

        assert result.iterations == 0
        assert result.message_latency_avg == 0.0
        assert result.tokens_per_response_avg == 0.0

    @pytest.mark.asyncio
    async def test_run_multiple_messages(self):
        """Test benchmark averages across multiple messages."""
        orchestrator = MagicMock()
        orchestrator.process_message = AsyncMock()
        orchestrator.process_message.side_effect = [
            (
                ChatMessage(role="assistant", content="First response here"),
                [CitationReference(report_id="r1", chunk_id="c1", score=0.95)] * 2,
            ),
            (
                ChatMessage(role="assistant", content="Second response with more tokens here"),
                [CitationReference(report_id="r1", chunk_id="c1", score=0.95)],
            ),
        ]

        benchmark = ChatBenchmark(orchestrator)
        result = await benchmark.run(
            session_id="s1",
            messages=["First msg", "Second msg"],
        )

        assert result.iterations == 2
        # First: 3 words, Second: 6 words → avg 4.5
        assert result.tokens_per_response_avg == 4.5
        # First: 2 citations, Second: 1 citation → avg 1.5
        assert result.citations_per_response_avg == 1.5

    def test_aggregate_empty(self):
        """Test aggregation with empty stats list."""
        benchmark = ChatBenchmark(MagicMock())
        result = benchmark._aggregate([])
        assert result.iterations == 0
        assert result.message_latency_avg == 0.0

    def test_aggregate_single(self):
        """Test aggregation with single stat entry."""
        benchmark = ChatBenchmark(MagicMock())
        stats = [
            {
                "message_index": 0,
                "total_latency_ms": 100.0,
                "retrieval_latency_ms": 20.0,
                "generation_latency_ms": 70.0,
                "tokens": 10,
                "citations": 2,
            }
        ]
        result = benchmark._aggregate(stats)
        assert result.iterations == 1
        assert result.message_latency_avg == 100.0
        assert result.retrieval_latency_avg == 20.0
        assert result.generation_latency_avg == 70.0
        assert result.tokens_per_response_avg == 10.0
        assert result.citations_per_response_avg == 2.0
