"""Tests for context benchmark framework."""

import pytest

from src.ai_core.context.base import ContextStrategy
from src.ai_core.context.benchmark import ContextBenchmark, ContextBenchmarkReport
from src.ai_core.context.models import ContextChunk, ConversationMessage, LLMContext
from src.ai_core.context.pipeline import ContextAssemblyPipeline


class _FixedStrategy(ContextStrategy):
    @property
    def strategy_name(self) -> str:
        return "fixed"

    async def assemble(self, query, chunks, history, config):
        return LLMContext(
            query=query,
            chunks=chunks,
            conversation_history=history,
        )

    def configure(self, params: dict) -> None:
        pass


class TestContextBenchmarkReport:
    def test_defaults(self):
        report = ContextBenchmarkReport()
        assert report.num_runs == 0
        assert report.total_time == 0.0

    def test_summary(self):
        report = ContextBenchmarkReport(
            pipeline_name="test",
            num_runs=5,
            total_time=2.0,
            mean_latency=0.4,
            mean_context_size=10.0,
            mean_token_usage=2000,
        )
        s = report.summary()
        assert "test" in s
        assert "0.400" in s


class TestContextBenchmark:
    @pytest.mark.asyncio
    async def test_benchmark_run(self):
        pipeline = ContextAssemblyPipeline(strategy=_FixedStrategy())
        bench = ContextBenchmark()
        report = await bench.run(
            pipeline,
            queries=["q1", "q2"],
            chunk_sets=[
                [ContextChunk(chunk_id="c1", content="a")],
                [ContextChunk(chunk_id="c2", content="b")],
            ],
        )
        assert report.num_runs == 2
        assert report.total_time > 0
        assert report.mean_latency > 0
        assert len(report.timing) == 2

    @pytest.mark.asyncio
    async def test_benchmark_with_histories(self):
        pipeline = ContextAssemblyPipeline(strategy=_FixedStrategy())
        bench = ContextBenchmark()
        report = await bench.run(
            pipeline,
            queries=["q"],
            chunk_sets=[
                [ContextChunk(chunk_id="c1", content="a")],
            ],
            histories=[
                [ConversationMessage(role="user", content="hi")],
            ],
        )
        assert report.num_runs == 1
        assert report.mean_context_size >= 1
