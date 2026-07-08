"""Tests for EmbeddingBenchmarkFramework."""

from src.ai_core.embedding.benchmark import EmbeddingBenchmarkFramework, EmbeddingBenchmarkReport


class _MockBenchmark:
    """Simple mock provider for benchmarking tests."""

    provider_name = "mock_bench"
    _model_name = "bench-model"

    @property
    def dimensions(self):
        return 3

    @property
    def model_name(self):
        return self._model_name

    async def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def configure(self, params: dict) -> None:
        pass

    async def health_check(self) -> bool:
        return True


class TestEmbeddingBenchmark:
    async def test_run(self):
        benchmark = EmbeddingBenchmarkFramework()
        provider = _MockBenchmark()
        texts = ["Hello world"] * 10
        report = await benchmark.run(provider, texts, batch_size=5, iterations=2)
        assert isinstance(report, EmbeddingBenchmarkReport)
        assert report.provider_name == "mock_bench"
        assert report.total_texts == 10
        assert report.batch_size == 5
        assert len(report.timing) == 2
        assert report.total_time > 0

    async def test_report_summary(self):
        report = EmbeddingBenchmarkReport(
            provider_name="test",
            model_name="test",
            dimensions=3,
            total_texts=10,
            batch_size=5,
            num_batches=2,
            timing=[0.1, 0.2],
            mean_latency=0.15,
            total_time=0.3,
            throughput=33.33,
        )
        summary = report.summary()
        assert "test" in summary
        assert "0.15" in summary
        assert "33.3" in summary

    async def test_compare(self):
        benchmark = EmbeddingBenchmarkFramework()
        provider = _MockBenchmark()
        texts = ["test"] * 5
        reports = await benchmark.compare([provider], texts)
        assert "mock_bench" in reports
        assert reports["mock_bench"].total_texts == 5
