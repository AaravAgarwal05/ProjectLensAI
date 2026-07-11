"""Benchmark framework for retrieval operations.

Collects:
- Latency (seconds)
- Recall@k
- Precision@k
- MRR (Mean Reciprocal Rank)
- NDCG (Normalised Discounted Cumulative Gain)
- Top-k hit rate
- Throughput (queries/second)
"""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from src.ai_core.retrieval.models import RetrievalResult, SearchQuery
from src.ai_core.retrieval.pipeline import RetrievalPipeline

logger = logging.getLogger(__name__)


@dataclass
class RetrievalBenchmarkReport:
    """Report from a single benchmark run.

    Attributes:
        pipeline_name: Name of the pipeline configuration.
        num_queries: Number of queries executed.
        total_time: Total wall-clock time.
        throughput: Queries per second.
        mean_latency: Mean latency per query.
        recall: Mean recall@k.
        precision: Mean precision@k.
        mrr: Mean Reciprocal Rank.
        ndcg: Mean NDCG.
        top_k_hit_rate: Fraction of queries with ≥1 relevant result.
        timing: Per-query latencies.
        errors: Per-query errors.
    """

    pipeline_name: str = ""
    num_queries: int = 0
    total_time: float = 0.0
    throughput: float = 0.0
    mean_latency: float = 0.0
    recall: float = 0.0
    precision: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    top_k_hit_rate: float = 0.0
    timing: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Benchmark: {self.pipeline_name}",
            f"  Queries:       {self.num_queries}",
            f"  Total time:    {self.total_time:.4f}s",
            f"  Throughput:    {self.throughput:.1f} q/s",
            f"  Mean latency:  {self.mean_latency:.4f}s",
            f"  Recall@k:      {self.recall:.4f}",
            f"  Precision@k:   {self.precision:.4f}",
            f"  MRR:           {self.mrr:.4f}",
            f"  NDCG:          {self.ndcg:.4f}",
            f"  Hit rate:      {self.top_k_hit_rate:.4f}",
        ]
        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for e in self.errors[:5]:
                lines.append(f"    - {e}")
        return "\n".join(lines)


class RetrievalBenchmark:
    """Benchmarks retrieval pipeline performance."""

    def __init__(self) -> None:
        self._timings: list[float] = []

    async def run(
        self,
        pipeline: RetrievalPipeline,
        queries: list[str],
        top_k: int = 10,
        relevance_fn: Callable[[str, str], bool] | None = None,
    ) -> RetrievalBenchmarkReport:
        """Run benchmark on a set of queries.

        Args:
            pipeline: The pipeline to benchmark.
            queries: List of query strings.
            top_k: Top-k for evaluation.
            relevance_fn: Optional ``(query, chunk_id) -> bool`` for relevance
                judgements.  If omitted, every result counts as relevant.

        Returns:
            A ``RetrievalBenchmarkReport``.
        """
        report = RetrievalBenchmarkReport(
            pipeline_name=(
                f"{pipeline.retriever.retriever_name}/"
                f"{pipeline.reranker.reranker_name if pipeline.reranker else 'none'}"
            ),
            num_queries=len(queries),
        )

        t0 = time.monotonic()
        recalls: list[float] = []
        precisions: list[float] = []
        mrrs: list[float] = []
        ndcgs: list[float] = []
        hit_rates: list[float] = []

        for q_text in queries:
            t1 = time.monotonic()
            query = SearchQuery(text=q_text, top_k=top_k)

            try:
                result: RetrievalResult = await pipeline.run(query)
                report.timing.append(time.monotonic() - t1)
            except Exception as exc:
                report.errors.append(f"Query '{q_text[:50]}...' failed: {exc}")
                continue

            chunks = result.chunks
            k = min(top_k, len(chunks))

            # Relevance judgements
            relevant: list[bool] = []
            if relevance_fn:
                for c in chunks[:k]:
                    relevant.append(relevance_fn(q_text, c.chunk_id))
            else:
                relevant = [True] * k if k > 0 else []

            n_relevant = sum(relevant)
            total_relevant = max(1, len(chunks))

            # Recall@k
            recalls.append(n_relevant / total_relevant)

            # Precision@k
            precisions.append(n_relevant / max(1, k))

            # Hit rate
            hit_rates.append(1.0 if n_relevant > 0 else 0.0)

            # MRR
            for rank, rel in enumerate(relevant, 1):
                if rel:
                    mrrs.append(1.0 / rank)
                    break
            else:
                mrrs.append(0.0)

            # NDCG
            dcg = sum(
                (1.0 / math.log2(rank + 1)) for rank, rel in enumerate(relevant[:k], 1) if rel
            )
            ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(n_relevant, k) + 1))
            ndcgs.append(dcg / ideal if ideal > 0 else 0.0)

        report.total_time = time.monotonic() - t0
        report.throughput = len(queries) / report.total_time if report.total_time > 0 else 0.0

        if report.timing:
            report.mean_latency = sum(report.timing) / len(report.timing)
        if recalls:
            report.recall = sum(recalls) / len(recalls)
        if precisions:
            report.precision = sum(precisions) / len(precisions)
        if mrrs:
            report.mrr = sum(mrrs) / len(mrrs)
        if ndcgs:
            report.ndcg = sum(ndcgs) / len(ndcgs)
        if hit_rates:
            report.top_k_hit_rate = sum(hit_rates) / len(hit_rates)

        return report
