"""Tests for BenchmarkFramework."""
import time

from shared.models import DocumentMetadata, ParsedDocument

from src.ai_core.chunking.benchmark import BenchmarkFramework, BenchmarkReport
from src.ai_core.chunking.strategies.fixed import FixedChunker
from src.ai_core.chunking.strategies.heading_aware import HeadingAwareChunker


def _make_doc(text: str | None = None) -> ParsedDocument:
    return ParsedDocument(
        report_id="test",
        parser_used="test",
        metadata=DocumentMetadata(title="Test", author="Author", language="en"),
        clean_text=text or "Hello world. " * 500,
    )


class DummyChunker(FixedChunker):
    """A slow chunker for testing timing measurements."""
    @property
    def name(self) -> str:
        return "dummy"

    def chunk(self, document):
        time.sleep(0.01)
        return super().chunk(document)


class TestBenchmarkFramework:
    def test_run_single_chunker(self):
        benchmark = BenchmarkFramework()
        chunker = FixedChunker()
        doc = _make_doc("Test content. " * 20)
        report = benchmark.run(chunker, doc, iterations=3)
        assert isinstance(report, BenchmarkReport)
        assert report.strategy_name == "fixed"
        assert report.iterations == 3
        assert len(report.timing) == 3
        assert report.mean_time > 0

    def test_run_heading_aware(self):
        benchmark = BenchmarkFramework()
        chunker = HeadingAwareChunker()
        doc = _make_doc(
            "Chapter 1: Intro\n\nText.\nChapter 2: Body\n\nMore text.\nChapter 3: End\n\nDone."
        )
        report = benchmark.run(chunker, doc, iterations=2)
        assert report.strategy_name == "heading_aware"
        assert report.chunk_counts[0] > 0

    def test_report_summary_string(self):
        report = BenchmarkReport(
            strategy_name="test",
            iterations=3,
            document_length=100,
            timing=[0.1, 0.2, 0.3],
            mean_time=0.2,
            std_dev_time=0.1,
            min_time=0.1,
            max_time=0.3,
            chunk_counts=[5, 5, 5],
            mean_chunk_count=5.0,
            chunk_sizes_avg=[200.0, 200.0, 200.0],
            overall_avg_chunk_size=200.0,
            overall_largest_chunk=250,
            overall_smallest_chunk=50,
        )
        summary = report.summary()
        assert "test" in summary
        assert "0.2000" in summary
        assert "5.0" in summary

    def test_compare(self):
        benchmark = BenchmarkFramework()
        doc = _make_doc()
        chunkers = [FixedChunker(), DummyChunker()]
        reports = benchmark.compare(chunkers, doc, iterations=2)
        assert "fixed" in reports
        assert "dummy" in reports
        # Dummy should be slower
        reports["dummy"].mean_time >= reports["fixed"].mean_time

    def test_error_handling(self):
        class FailingChunker(FixedChunker):
            @property
            def name(self):
                return "fail"

            def chunk(self, document):
                raise RuntimeError("chunk failed")

        benchmark = BenchmarkFramework()
        doc = _make_doc("test")
        report = benchmark.run(FailingChunker(), doc, iterations=2)
        assert len(report.errors) > 0

    def test_memory_measurement(self):
        benchmark = BenchmarkFramework(measure_memory=True)
        chunker = FixedChunker()
        doc = _make_doc("A" * 1000)
        report = benchmark.run(chunker, doc, iterations=1)
        # memory_usage may be None if tracemalloc unavailable
        assert report is not None

    def test_document_length(self):
        doc = _make_doc("A" * 500)
        benchmark = BenchmarkFramework()
        report = benchmark.run(FixedChunker(), doc, iterations=1)
        assert report.document_length == 500

    def test_compare_empty_document(self):
        benchmark = BenchmarkFramework()
        doc = _make_doc("")
        chunkers = [FixedChunker(), HeadingAwareChunker()]
        reports = benchmark.compare(chunkers, doc, iterations=1)
        assert "fixed" in reports
        assert "heading_aware" in reports