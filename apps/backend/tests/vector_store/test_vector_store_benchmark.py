"""Tests for VectorStoreBenchmark."""

from src.ai_core.vector_store.benchmark import VectorStoreBenchmark, VectorStoreBenchmarkReport
from src.ai_core.vector_store.providers.chroma_store import ChromaVectorStore


class TestVectorStoreBenchmark:
    async def test_run_insert(self):
        store = ChromaVectorStore()
        bench = VectorStoreBenchmark()
        report = await bench.run_insert(
            store=store,
            collection="bench_insert",
            num_documents=20,
            dimensions=4,
            batch_size=5,
        )
        assert report.store_name == "chroma"
        assert report.operation == "insert"
        assert report.total_documents == 20
        assert report.num_batches > 0
        assert report.total_time > 0
        assert report.throughput > 0

    async def test_report_summary(self):
        report = VectorStoreBenchmarkReport(
            store_name="chroma",
            operation="insert",
            total_documents=100,
            batch_size=10,
            num_batches=10,
            total_time=1.5,
            throughput=66.67,
            mean_latency=0.15,
            collection_name="test",
        )
        summary = report.summary()
        assert "chroma" in summary
        assert "66.7" in summary
        assert "0.15" in summary

    async def test_run_update(self):
        store = ChromaVectorStore()
        bench = VectorStoreBenchmark()
        report = await bench.run_update(
            store=store,
            collection="bench_update",
            num_documents=20,
            dimensions=4,
            batch_size=5,
        )
        assert report.operation == "update"
        assert report.total_documents == 20

    async def test_run_delete(self):
        store = ChromaVectorStore()
        bench = VectorStoreBenchmark()
        report = await bench.run_delete(
            store=store,
            collection="bench_delete",
            num_documents=20,
            dimensions=4,
            batch_size=5,
        )
        assert report.operation == "delete"
