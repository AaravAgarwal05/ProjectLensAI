"""Benchmark framework for embedding providers.

Measures:
- Embedding latency (per-batch wall-clock).
- Batch throughput (chunks/second).
- Memory usage (optional).
- Embedding dimensions, provider name, model name.

Typical usage::

    benchmark = EmbeddingBenchmark()
    report = await benchmark.run(provider, texts=["...", "..."], batch_size=32)
    print(report.summary())
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from src.ai_core.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingBenchmarkReport:
    """Report from a single benchmark run.

    Attributes:
        provider_name: Name of the provider.
        model_name: Model identifier.
        dimensions: Vector dimensionality.
        total_texts: Number of texts embedded.
        batch_size: Texts per batch.
        timing: Per-batch wall-clock times (seconds).
        mean_latency: Mean batch latency.
        total_time: Total wall-clock time.
        throughput: Texts per second.
        memory_usage: Peak memory delta (bytes, optional).
        errors: Any errors during runs.
    """

    provider_name: str = ""
    model_name: str = ""
    dimensions: int = 0
    total_texts: int = 0
    batch_size: int = 0
    num_batches: int = 0
    timing: list[float] = field(default_factory=list)
    mean_latency: float = 0.0
    total_time: float = 0.0
    throughput: float = 0.0
    memory_usage: int | None = None
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Benchmark: {self.provider_name} / {self.model_name}",
            f"  Dimensions:      {self.dimensions}",
            f"  Total texts:     {self.total_texts}",
            f"  Batch size:      {self.batch_size}",
            f"  Batches:         {self.num_batches}",
            "  Timing:",
            f"    Mean latency:  {self.mean_latency:.4f}s",
            f"    Total time:    {self.total_time:.4f}s",
            f"    Throughput:    {self.throughput:.1f} texts/s",
        ]
        if self.memory_usage is not None:
            kb = self.memory_usage / 1024
            mb = self.memory_usage / (1024 * 1024)
            lines.append(f"  Memory: {mb:.1f} MB ({kb:.1f} KB)")
        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for e in self.errors[:5]:
                lines.append(f"    - {e}")
        return "\n".join(lines)


class EmbeddingBenchmarkFramework:
    """Benchmarks embedding providers for performance.

    Runs the provider's ``embed_batch`` method across the given texts.
    """

    WARMUP_BATCHES = 1

    def __init__(self, measure_memory: bool = False) -> None:
        """Initialize.

        Args:
            measure_memory: Track memory via ``tracemalloc``.  Adds overhead.
        """
        self._measure_memory = measure_memory

    async def run(
        self,
        provider: EmbeddingProvider,
        texts: list[str],
        batch_size: int = 32,
        iterations: int = 3,
    ) -> EmbeddingBenchmarkReport:
        """Benchmark *provider* on *texts*.

        Args:
            provider: An ``EmbeddingProvider`` instance.
            texts: Input texts to embed.
            batch_size: Texts per batch.
            iterations: Number of measurement runs (1 for large datasets).

        Returns:
            An ``EmbeddingBenchmarkReport``.
        """
        report = EmbeddingBenchmarkReport(
            provider_name=provider.provider_name,
            model_name=provider.model_name,
            dimensions=provider.dimensions,
            total_texts=len(texts),
            batch_size=batch_size,
        )

        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
        report.num_batches = len(batches)

        # Warm-up
        for batch in batches[: max(1, self.WARMUP_BATCHES)]:
            try:
                await provider.embed_batch(batch)
            except Exception as exc:
                logger.warning("Warm-up batch failed: %s", exc)

        # Measurement
        for iteration in range(iterations):
            if self._measure_memory:
                import tracemalloc

                tracemalloc.start()

            t0 = time.monotonic()
            try:
                for batch in batches:
                    await provider.embed_batch(batch)
                elapsed = time.monotonic() - t0
                report.timing.append(elapsed)
            except Exception as exc:
                report.errors.append(f"Iteration {iteration}: {exc}")

            if self._measure_memory:
                _current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                if report.memory_usage is None:
                    report.memory_usage = peak
                else:
                    report.memory_usage = max(report.memory_usage, peak)

        # Compute aggregates
        if report.timing:
            report.mean_latency = sum(report.timing) / len(report.timing)
        report.total_time = sum(report.timing) if report.timing else 0
        if report.total_time > 0:
            report.throughput = (len(texts) * iterations) / report.total_time

        return report

    async def compare(
        self,
        providers: list[EmbeddingProvider],
        texts: list[str],
        batch_size: int = 32,
    ) -> dict[str, EmbeddingBenchmarkReport]:
        """Benchmark multiple providers on the same texts."""
        reports: dict[str, EmbeddingBenchmarkReport] = {}
        for provider in providers:
            reports[provider.provider_name] = await self.run(
                provider, texts, batch_size, iterations=1
            )
        return reports
