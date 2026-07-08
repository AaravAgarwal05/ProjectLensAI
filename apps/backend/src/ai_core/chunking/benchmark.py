"""Benchmark framework for chunking strategies.

Measures:
- Processing time (wall-clock per run).
- Memory usage (optional, via ``tracemalloc`` or ``resource``).
- Chunk statistics (count, sizes, tokens).
- Standard deviation across multiple runs.

Typical usage::

    benchmark = BenchmarkFramework()
    report = benchmark.run(chunker, document, iterations=5)
    print(report.summary())
"""

from __future__ import annotations

import logging
import statistics
import time
from dataclasses import dataclass, field

from shared.models.processing import ParsedDocument

from src.ai_core.chunking.base import ChunkingStrategy
from src.ai_core.chunking.models import ChunkingResult

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkReport:
    """Report from a single benchmark run.

    Attributes:
        strategy_name: Name of the chunker that was benchmarked.
        iterations: Number of runs.
        document_length: Character count of the input document.
        timing: Per-iteration wall-clock times (seconds).
        mean_time: Mean wall-clock time (seconds).
        std_dev_time: Standard deviation of wall-clock times.
        min_time: Fastest single run (seconds).
        max_time: Slowest single run (seconds).
        chunk_counts: Per-iteration chunk count.
        mean_chunk_count: Mean chunk count.
        chunk_sizes_avg: Per-iteration average chunk size.
        overall_avg_chunk_size: Mean of average chunk sizes.
        overall_largest_chunk: Largest single chunk across all runs.
        overall_smallest_chunk: Smallest single chunk across all runs.
        memory_usage: Estimated memory delta (bytes), if measured.
        errors: Any errors encountered during runs.
    """

    strategy_name: str = ""
    iterations: int = 0
    document_length: int = 0
    timing: list[float] = field(default_factory=list)
    mean_time: float = 0.0
    std_dev_time: float = 0.0
    min_time: float = 0.0
    max_time: float = 0.0
    chunk_counts: list[int] = field(default_factory=list)
    mean_chunk_count: float = 0.0
    chunk_sizes_avg: list[float] = field(default_factory=list)
    overall_avg_chunk_size: float = 0.0
    overall_largest_chunk: int = 0
    overall_smallest_chunk: int = 0
    memory_usage: int | None = None
    errors: list[str] = field(default_factory=list)
    raw_results: list[ChunkingResult] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Benchmark: {self.strategy_name}",
            f"  Iterations:      {self.iterations}",
            f"  Document length: {self.document_length} chars",
            "  Timing:",
            f"    Mean:   {self.mean_time:.4f}s",
            f"    StdDev: {self.std_dev_time:.4f}s",
            f"    Min:    {self.min_time:.4f}s",
            f"    Max:    {self.max_time:.4f}s",
            "  Chunks:",
            f"    Mean count:     {self.mean_chunk_count:.1f}",
            f"    Mean size:      {self.overall_avg_chunk_size:.1f} chars",
            f"    Largest:        {self.overall_largest_chunk} chars",
            f"    Smallest:       {self.overall_smallest_chunk} chars",
        ]
        if self.memory_usage is not None:
            lines.append(f"  Memory: {self._format_bytes(self.memory_usage)}")
        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for e in self.errors[:5]:
                lines.append(f"    - {e}")
        return "\n".join(lines)

    @staticmethod
    def _format_bytes(b: int) -> str:
        if b < 1024:
            return f"{b} B"
        elif b < 1024**2:
            return f"{b / 1024:.1f} KB"
        else:
            return f"{b / 1024**2:.1f} MB"


class BenchmarkFramework:
    """Benchmarks chunking strategies for performance and consistency.

    Runs the chunker N times on the same document and aggregates
    timing, chunk statistics, and memory usage.
    """

    # Warm-up iterations before measurement
    WARMUP_ITERATIONS = 1

    def __init__(
        self,
        measure_memory: bool = False,
        warmup: int | None = None,
    ) -> None:
        """Initialize the benchmark framework.

        Args:
            measure_memory: Track memory usage via ``tracemalloc``.
                            Adds overhead — disable for accurate timing.
            warmup: Number of warm-up iterations.  Defaults to
                    ``WARMUP_ITERATIONS``.
        """
        self._measure_memory = measure_memory
        self._warmup = warmup if warmup is not None else self.WARMUP_ITERATIONS

    def run(
        self,
        chunker: ChunkingStrategy,
        document: ParsedDocument,
        iterations: int = 3,
    ) -> BenchmarkReport:
        """Benchmark *chunker* on *document*.

        Args:
            chunker: A chunking strategy instance.
            document: The parsed document to chunk.
            iterations: Number of measurement runs (default 3).

        Returns:
            A ``BenchmarkReport`` with aggregated results.
        """
        report = BenchmarkReport(
            strategy_name=chunker.name,
            iterations=iterations,
            document_length=len(document.clean_text) if document.clean_text else 0,
        )

        # Warm-up
        for _ in range(self._warmup):
            try:
                chunker.chunk(document)
            except Exception as exc:
                logger.warning("Warm-up chunking failed: %s", exc)

        # Measurement runs
        largest = 0
        smallest = float("inf")

        for iteration in range(iterations):
            try:
                if self._measure_memory:
                    import tracemalloc

                    tracemalloc.start()
                    t0 = time.monotonic()
                    result = chunker.chunk(document)
                    elapsed = time.monotonic() - t0
                    _snapshot = tracemalloc.take_snapshot()
                    # We only track the delta from the start; the full
                    # snapshot comparison is expensive so we record the
                    # current traced memory instead.
                    _current, _peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    if report.memory_usage is None:
                        report.memory_usage = _peak
                    else:
                        report.memory_usage = max(report.memory_usage, _peak)
                else:
                    t0 = time.monotonic()
                    result = chunker.chunk(document)
                    elapsed = time.monotonic() - t0

                report.timing.append(elapsed)
                report.chunk_counts.append(len(result.chunks))
                report.raw_results.append(result)

                if result.chunks:
                    sizes = [len(c.text) for c in result.chunks]
                    report.chunk_sizes_avg.append(sum(sizes) / len(sizes))
                    largest = max(largest, max(sizes))
                    smallest = min(smallest, min(sizes))
                else:
                    report.chunk_sizes_avg.append(0.0)

            except Exception as exc:
                report.errors.append(f"Iteration {iteration}: {exc}")
                logger.exception("Benchmark iteration %d failed", iteration)

        # Compute aggregates
        if report.timing:
            report.mean_time = statistics.mean(report.timing)
            if len(report.timing) > 1:
                report.std_dev_time = statistics.stdev(report.timing)
            report.min_time = min(report.timing)
            report.max_time = max(report.timing)

        if report.chunk_counts:
            report.mean_chunk_count = statistics.mean(report.chunk_counts)

        if report.chunk_sizes_avg:
            report.overall_avg_chunk_size = statistics.mean(report.chunk_sizes_avg)

        report.overall_largest_chunk = largest if largest > 0 else 0
        report.overall_smallest_chunk = int(smallest) if smallest != float("inf") else 0

        return report

    def compare(
        self,
        chunkers: list[ChunkingStrategy],
        document: ParsedDocument,
        iterations: int = 3,
    ) -> dict[str, BenchmarkReport]:
        """Benchmark multiple chunkers on the same document.

        Args:
            chunkers: List of chunker instances.
            document: The parsed document.
            iterations: Runs per chunker.

        Returns:
            Dict mapping strategy name to ``BenchmarkReport``.
        """
        reports: dict[str, BenchmarkReport] = {}
        for chunker in chunkers:
            reports[chunker.name] = self.run(chunker, document, iterations)
        return reports
