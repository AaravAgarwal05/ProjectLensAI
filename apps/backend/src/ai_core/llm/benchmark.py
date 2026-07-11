"""Benchmark framework for LLM generation."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from statistics import mean

from src.ai_core.llm.base import LLMProvider
from src.ai_core.llm.models import (
    GenerationStatistics,
    LLMRequest,
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    iterations: int = 0
    prompt_tokens_avg: float = 0.0
    completion_tokens_avg: float = 0.0
    total_tokens_avg: float = 0.0
    tokens_per_second_avg: float = 0.0
    time_to_first_token_ms_avg: float = 0.0
    total_latency_ms_avg: float = 0.0
    memory_usage_mb_avg: float = 0.0
    individual: list[GenerationStatistics] = field(default_factory=list)


class LLMBenchmark:
    """Runs performance benchmarks against an LLM provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def run(
        self,
        request: LLMRequest,
        iterations: int = 3,
        collect_memory: bool = True,
    ) -> BenchmarkResult:
        """Run *iterations* generations and collect metrics.

        Args:
            request: The generation request to benchmark.
            iterations: Number of runs.
            collect_memory: Whether to measure memory usage.

        Returns:
            Aggregated benchmark result.
        """
        import psutil

        stats_list: list[GenerationStatistics] = []
        process = psutil.Process()

        for i in range(iterations):
            logger.info("Benchmark iteration %d/%d", i + 1, iterations)

            mem_before = process.memory_info().rss / (1024 * 1024) if collect_memory else 0.0

            # Non-streaming latency
            start = time.monotonic()
            response = await self._provider.generate(request)
            total_latency = (time.monotonic() - start) * 1000

            mem_after = process.memory_info().rss / (1024 * 1024) if collect_memory else 0.0
            mem_usage = max(0.0, mem_after - mem_before)

            # Streaming — measure time-to-first-token
            ttft: float = 0.0
            stream_chunks: list[str] = []
            try:
                request.stream = True
                start = time.monotonic()
                async for chunk in self._provider.generate_stream(request):
                    if not ttft and chunk.text:
                        ttft = (time.monotonic() - start) * 1000
                    stream_chunks.append(chunk.text)
                    if chunk.finish_reason:
                        break
            finally:
                request.stream = False

            completion_tokens = response.metadata.token_usage.completion_tokens

            tps = 0.0
            if total_latency > 0 and completion_tokens > 0:
                tps = (completion_tokens / total_latency) * 1000

            stats = GenerationStatistics(
                prompt_tokens=response.metadata.token_usage.prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=response.metadata.token_usage.total_tokens,
                tokens_per_second=tps,
                time_to_first_token_ms=ttft,
                total_latency_ms=total_latency,
                memory_usage_mb=mem_usage,
            )
            stats_list.append(stats)

        return self._aggregate(stats_list)

    def _aggregate(self, stats_list: list[GenerationStatistics]) -> BenchmarkResult:
        """Compute averages across iterations."""
        n = len(stats_list)
        if n == 0:
            return BenchmarkResult()

        return BenchmarkResult(
            iterations=n,
            prompt_tokens_avg=mean(s.prompt_tokens for s in stats_list),
            completion_tokens_avg=mean(s.completion_tokens for s in stats_list),
            total_tokens_avg=mean(s.total_tokens for s in stats_list),
            tokens_per_second_avg=mean(s.tokens_per_second for s in stats_list),
            time_to_first_token_ms_avg=mean(s.time_to_first_token_ms for s in stats_list),
            total_latency_ms_avg=mean(s.total_latency_ms for s in stats_list),
            memory_usage_mb_avg=mean(s.memory_usage_mb for s in stats_list),
            individual=stats_list,
        )
