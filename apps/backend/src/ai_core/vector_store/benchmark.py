"""Benchmark framework for vector-store operations.

Measures:
- Insert throughput (documents/second).
- Delete throughput (documents/second).
- Update throughput (documents/second).
- Memory usage (optional).
- Storage size (per-collection, when available).
- Latency per batch.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from src.ai_core.vector_store.base import VectorStore
from src.ai_core.vector_store.models import VectorDocument, VectorMetadata

logger = logging.getLogger(__name__)


@dataclass
class VectorStoreBenchmarkReport:
    """Report from a single benchmark run.

    Attributes:
        store_name: Name of the store provider.
        operation: Operation measured (insert/delete/update).
        total_documents: Number of documents processed.
        batch_size: Documents per batch.
        total_time: Total wall-clock time.
        throughput: Documents per second.
        mean_latency: Mean batch latency (seconds).
        memory_usage: Peak memory delta (bytes, optional).
        collection_name: Target collection.
    """

    store_name: str = ""
    operation: str = ""
    total_documents: int = 0
    batch_size: int = 0
    num_batches: int = 0
    total_time: float = 0.0
    throughput: float = 0.0
    mean_latency: float = 0.0
    timing: list[float] = field(default_factory=list)
    memory_usage: int | None = None
    collection_name: str = ""
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Benchmark: {self.store_name} / {self.operation}",
            f"  Collection:      {self.collection_name}",
            f"  Total documents: {self.total_documents}",
            f"  Batch size:      {self.batch_size}",
            f"  Batches:         {self.num_batches}",
            f"  Total time:      {self.total_time:.4f}s",
            f"  Throughput:      {self.throughput:.1f} docs/s",
            f"  Mean latency:    {self.mean_latency:.4f}s",
        ]
        if self.memory_usage is not None:
            mb = self.memory_usage / (1024 * 1024)
            lines.append(f"  Memory:          {mb:.1f} MB")
        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for e in self.errors[:5]:
                lines.append(f"    - {e}")
        return "\n".join(lines)


class VectorStoreBenchmark:
    """Benchmarks vector-store operations.

    Runs the store's insert/delete/update methods across generated documents.
    """

    def __init__(self, measure_memory: bool = False) -> None:
        self._measure_memory = measure_memory

    async def run_insert(
        self,
        store: VectorStore,
        collection: str,
        num_documents: int = 100,
        dimensions: int = 4,
        batch_size: int = 10,
    ) -> VectorStoreBenchmarkReport:
        """Benchmark insert performance."""
        await store.create_collection(collection, dimensions=dimensions)
        report = await self._run(
            store=store,
            collection=collection,
            batch_size=batch_size,
            num_documents=num_documents,
            dimensions=dimensions,
            operation="insert",
            store_fn=lambda col, docs: store.insert(col, docs),
        )
        return report

    async def run_delete(
        self,
        store: VectorStore,
        collection: str,
        num_documents: int = 100,
        dimensions: int = 4,
        batch_size: int = 10,
    ) -> VectorStoreBenchmarkReport:
        """Benchmark delete performance (by chunk_id)."""
        # Pre-populate
        await store.create_collection(collection, dimensions=dimensions)
        all_docs = _generate_docs(0, num_documents, dimensions)
        await store.insert(collection, all_docs)

        report = await self._run(
            store=store,
            collection=collection,
            batch_size=batch_size,
            num_documents=num_documents,
            dimensions=dimensions,
            operation="delete",
            generate_fn=lambda start, count: [
                {"chunk_ids": [f"chunk_{i}" for i in range(start, start + count)]}
            ],
            store_fn=lambda col, batch: store.delete(col, chunk_ids=batch["chunk_ids"]),
        )
        return report

    async def run_update(
        self,
        store: VectorStore,
        collection: str,
        num_documents: int = 100,
        dimensions: int = 4,
        batch_size: int = 10,
    ) -> VectorStoreBenchmarkReport:
        """Benchmark update performance."""
        # Pre-populate
        await store.create_collection(collection, dimensions=dimensions)
        docs = _generate_docs(0, num_documents, dimensions)
        await store.insert(collection, docs)

        report = await self._run(
            store=store,
            collection=collection,
            batch_size=batch_size,
            num_documents=num_documents,
            dimensions=dimensions,
            operation="update",
            store_fn=lambda col, docs: store.update(col, docs),
        )
        return report

    async def _run(
        self,
        store: VectorStore,
        collection: str,
        batch_size: int,
        num_documents: int,
        dimensions: int,
        operation: str,
        store_fn: Callable[..., Any],
        generate_fn: Callable[..., Any] | None = None,
    ) -> VectorStoreBenchmarkReport:
        report = VectorStoreBenchmarkReport(
            store_name=store.store_name,
            operation=operation,
            total_documents=num_documents,
            batch_size=batch_size,
            collection_name=collection,
        )

        # Generate batches
        batches = [
            range(start, min(start + batch_size, num_documents))
            for start in range(0, num_documents, batch_size)
        ]
        report.num_batches = len(batches)

        if self._measure_memory:
            import tracemalloc

            tracemalloc.start()

        # Measurement
        t0 = time.monotonic()
        for batch_range in batches:
            start_id = batch_range[0]
            count = len(batch_range)

            if generate_fn:
                for batch_args in generate_fn(start_id, count):
                    try:
                        t1 = time.monotonic()
                        await store_fn(collection, batch_args)
                        report.timing.append(time.monotonic() - t1)
                        report.total_time = time.monotonic() - t0
                    except Exception as exc:
                        report.errors.append(str(exc))
            else:
                docs = _generate_docs(start_id, count, dimensions)
                try:
                    t1 = time.monotonic()
                    await store_fn(collection, docs)
                    report.timing.append(time.monotonic() - t1)
                    report.total_time = time.monotonic() - t0
                except Exception as exc:
                    report.errors.append(str(exc))

        if self._measure_memory:
            _current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            report.memory_usage = peak

        if report.timing:
            report.mean_latency = sum(report.timing) / len(report.timing)
        if report.total_time > 0:
            report.throughput = num_documents / report.total_time

        return report


def _generate_docs(start_id: int, count: int, dimensions: int) -> list[VectorDocument]:
    """Generate test documents with deterministic vectors."""
    docs: list[VectorDocument] = []
    for i in range(count):
        idx = start_id + i
        vec = [float((i + j) % 10) / 10.0 for j in range(dimensions)]
        docs.append(
            VectorDocument(
                chunk_id=f"chunk_{idx}",
                vector=vec,
                dimensions=dimensions,
                metadata=VectorMetadata(
                    chunk_id=f"chunk_{idx}",
                    report_id=f"report_{idx % 5}",
                    version_id=f"version_{idx % 3}",
                ),
            )
        )
    return docs
