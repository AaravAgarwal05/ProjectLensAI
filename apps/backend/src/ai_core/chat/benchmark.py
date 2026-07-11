"""Benchmark framework for chat operations."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from statistics import mean
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChatBenchmarkResult:
    """Result of a chat benchmark run."""

    iterations: int = 0
    message_latency_avg: float = 0.0
    retrieval_latency_avg: float = 0.0
    generation_latency_avg: float = 0.0
    tokens_per_response_avg: float = 0.0
    citations_per_response_avg: float = 0.0
    conversation_length_avg: float = 0.0
    individual: list[dict[str, Any]] = field(default_factory=list)


class ChatBenchmark:
    """Runs benchmarks on chat operations."""

    def __init__(self, orchestrator: Any) -> None:
        self._orchestrator = orchestrator

    async def run(
        self,
        session_id: str,
        messages: list[str],
        retrieve_chunks: Any = None,
    ) -> ChatBenchmarkResult:
        """Run benchmark iterations.

        Args:
            session_id: Session to benchmark against.
            messages: List of messages to process sequentially.
            retrieve_chunks: Retrieval callable.

        Returns:
            Aggregated benchmark result.
        """
        stats_list: list[dict[str, Any]] = []

        for i, msg in enumerate(messages):
            logger.info("Chat benchmark message %d/%d", i + 1, len(messages))

            total_start = time.monotonic()
            retrieval_start = time.monotonic()

            # Simulate retrieval timing (if chunks are retrieved)
            retrieval_latency = 0.0
            if retrieve_chunks:
                retrieval_start = time.monotonic()
                _ = retrieve_chunks(msg, [], 10)
                retrieval_latency = (time.monotonic() - retrieval_start) * 1000

            # Process message
            gen_start = time.monotonic()
            assistant_msg, citations = await self._orchestrator.process_message(
                session_id=session_id,
                user_message=msg,
                retrieve_chunks=retrieve_chunks,
            )
            gen_latency = (time.monotonic() - gen_start) * 1000
            total_latency = (time.monotonic() - total_start) * 1000

            token_estimate = len(assistant_msg.content.split())
            stats_list.append(
                {
                    "message_index": i,
                    "total_latency_ms": total_latency,
                    "retrieval_latency_ms": retrieval_latency,
                    "generation_latency_ms": gen_latency,
                    "tokens": token_estimate,
                    "citations": len(citations),
                }
            )

        return self._aggregate(stats_list)

    def _aggregate(self, stats_list: list[dict[str, Any]]) -> ChatBenchmarkResult:
        n = len(stats_list)
        if n == 0:
            return ChatBenchmarkResult()

        return ChatBenchmarkResult(
            iterations=n,
            message_latency_avg=mean(s["total_latency_ms"] for s in stats_list),
            retrieval_latency_avg=mean(s["retrieval_latency_ms"] for s in stats_list),
            generation_latency_avg=mean(s["generation_latency_ms"] for s in stats_list),
            tokens_per_response_avg=mean(s["tokens"] for s in stats_list),
            citations_per_response_avg=mean(s["citations"] for s in stats_list),
            conversation_length_avg=n,
            individual=stats_list,
        )
