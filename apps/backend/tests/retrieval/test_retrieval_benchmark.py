"""Tests for retrieval benchmark framework."""

from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.benchmark import RetrievalBenchmark, RetrievalBenchmarkReport
from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk, SearchQuery
from src.ai_core.retrieval.pipeline import RetrievalPipeline


class _FixedRetriever(Retriever):
    @property
    def retriever_name(self) -> str:
        return "fixed"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        return RetrievalResult(
            chunks=[
                RetrievedChunk(chunk_id=f"c{i}", content="x", score=1.0 / (i + 1))
                for i in range(query.top_k or 5)
            ],
            successful=True,
        )

    def configure(self, params: dict) -> None:
        pass


class _FilteredRetriever(Retriever):
    """Only returns c1 as relevant."""

    @property
    def retriever_name(self) -> str:
        return "filtered"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        return RetrievalResult(
            chunks=[
                RetrievedChunk(chunk_id="c1", content="relevant", score=0.95),
                RetrievedChunk(chunk_id="c2", content="irrelevant", score=0.3),
                RetrievedChunk(chunk_id="c3", content="noise", score=0.2),
            ],
            successful=True,
        )

    def configure(self, params: dict) -> None:
        pass


class TestRetrievalBenchmark:
    async def test_report_defaults(self):
        report = RetrievalBenchmarkReport()
        assert report.num_queries == 0
        assert report.total_time == 0.0
        assert report.recall == 0.0

    async def test_report_summary(self):
        report = RetrievalBenchmarkReport(
            pipeline_name="dense/none",
            num_queries=10,
            total_time=2.5,
            throughput=4.0,
            mean_latency=0.25,
            recall=0.8,
            precision=0.7,
            mrr=0.9,
            ndcg=0.85,
            top_k_hit_rate=0.95,
        )
        summary = report.summary()
        assert "dense" in summary
        assert "0.80" in summary or "0.8" in summary
        assert "4.0" in summary

    async def test_benchmark_run(self):
        pipeline = RetrievalPipeline(retriever=_FixedRetriever())
        bench = RetrievalBenchmark()
        report = await bench.run(pipeline, ["query1", "query2"], top_k=5)
        assert report.num_queries == 2
        assert report.total_time > 0
        assert report.mean_latency > 0
        assert len(report.timing) == 2

    async def test_benchmark_with_relevance(self):
        pipeline = RetrievalPipeline(retriever=_FilteredRetriever())
        bench = RetrievalBenchmark()

        def relevant(query: str, chunk_id: str) -> bool:
            return chunk_id == "c1"

        report = await bench.run(pipeline, ["find c1"], top_k=3, relevance_fn=relevant)
        assert report.recall > 0
        assert report.precision > 0
        assert report.mrr == 1.0  # c1 is first
