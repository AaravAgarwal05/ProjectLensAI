"""Benchmark framework for context assembly."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import (
    ContextChunk,
    ConversationMessage,
    LLMContext,
)
from src.ai_core.context.pipeline import ContextAssemblyPipeline

logger = logging.getLogger(__name__)


@dataclass
class ContextBenchmarkReport:
    """Report from a single benchmark run."""

    pipeline_name: str = ""
    num_runs: int = 0
    total_time: float = 0.0
    mean_latency: float = 0.0
    mean_context_size: float = 0.0
    mean_token_usage: float = 0.0
    mean_history_utilization: float = 0.0
    mean_retrieval_utilization: float = 0.0
    timing: list[float] = field(default_factory=list)
    contexts: list[LLMContext] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"ContextBenchmark(pipeline={self.pipeline_name}, "
            f"runs={self.num_runs}, "
            f"latency={self.mean_latency:.3f}s, "
            f"ctx_size={self.mean_context_size:.1f}, "
            f"tokens={self.mean_token_usage:.0f})"
        )


class ContextBenchmark:
    """Benchmark context assembly pipeline performance."""

    async def run(
        self,
        pipeline: ContextAssemblyPipeline,
        queries: list[str],
        chunk_sets: list[list[ContextChunk]],
        histories: list[list[ConversationMessage]] | None = None,
        config: ContextConfiguration | None = None,
    ) -> ContextBenchmarkReport:
        cfg = config or ContextConfiguration.default()
        histories = histories or [[] for _ in queries]
        report = ContextBenchmarkReport(pipeline_name="context_assembly")

        start = time.monotonic()
        for query, chunks, history in zip(queries, chunk_sets, histories, strict=False):
            t0 = time.monotonic()
            ctx = await pipeline.run(query=query, chunks=chunks, history=history, config=cfg)
            elapsed = time.monotonic() - t0
            report.timing.append(elapsed)
            report.contexts.append(ctx)

        report.total_time = time.monotonic() - start
        report.num_runs = len(queries)
        report.mean_latency = sum(report.timing) / len(report.timing) if report.timing else 0.0
        report.mean_context_size = (
            sum(c.metadata.num_chunks for c in report.contexts) / len(report.contexts)
            if report.contexts
            else 0.0
        )
        report.mean_token_usage = (
            sum(c.metadata.total_tokens for c in report.contexts) / len(report.contexts)
            if report.contexts
            else 0.0
        )
        report.mean_history_utilization = (
            sum(c.statistics.history_utilization for c in report.contexts) / len(report.contexts)
            if report.contexts
            else 0.0
        )
        report.mean_retrieval_utilization = (
            sum(c.statistics.retrieval_utilization for c in report.contexts) / len(report.contexts)
            if report.contexts
            else 0.0
        )

        return report
