"""Tests for LLMBenchmark."""

from __future__ import annotations

import pytest

from src.ai_core.llm.base import LLMProvider
from src.ai_core.llm.benchmark import LLMBenchmark
from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.models import (
    GenerationMetadata,
    LLMRequest,
    LLMResponse,
    StreamingChunk,
    TokenUsage,
)


class _BenchmarkProvider(LLMProvider):
    """A test provider with controllable timing for benchmarks."""

    def __init__(self) -> None:
        super().__init__(LLMConfiguration(timeout=5.0))

    @property
    def provider_name(self) -> str:
        return "bench"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        import asyncio

        await asyncio.sleep(0.01)
        return LLMResponse(
            text="Benchmark response",
            metadata=GenerationMetadata(
                latency_ms=10.0,
                token_usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
            ),
        )

    async def generate_stream(self, request: LLMRequest):
        import asyncio

        await asyncio.sleep(0.005)
        yield StreamingChunk(text="Benchmark")
        await asyncio.sleep(0.005)
        yield StreamingChunk(text=" response")
        yield StreamingChunk(text="", finish_reason="stop")

    async def check_health(self):
        return None  # pragma: no cover

    async def count_tokens(self, text: str) -> int:
        return 0  # pragma: no cover

    async def is_model_available(self, model_name: str) -> bool:
        return True  # pragma: no cover


class _NoMemProviderResponses(LLMProvider):
    """Provider that returns empty responses (edge case)."""

    def __init__(self) -> None:
        super().__init__(LLMConfiguration(timeout=5.0))

    @property
    def provider_name(self) -> str:
        return "empty"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            text="",
            metadata=GenerationMetadata(
                token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            ),
        )

    async def generate_stream(self, request: LLMRequest):
        yield StreamingChunk(text="", finish_reason="stop")

    async def check_health(self):
        return None  # pragma: no cover

    async def count_tokens(self, text: str) -> int:
        return 0  # pragma: no cover

    async def is_model_available(self, model_name: str) -> bool:
        return True  # pragma: no cover


class TestLLMBenchmark:
    @pytest.mark.asyncio
    async def test_benchmark_run(self):
        """Test benchmark collects metrics correctly."""
        provider = _BenchmarkProvider()
        benchmark = LLMBenchmark(provider)
        request = LLMRequest(user_prompt="Test benchmark")

        result = await benchmark.run(request, iterations=2, collect_memory=False)
        assert result.iterations == 2
        assert result.prompt_tokens_avg == 5.0
        assert result.completion_tokens_avg == 3.0
        assert result.total_tokens_avg == 8.0
        assert len(result.individual) == 2

    @pytest.mark.asyncio
    async def test_benchmark_zero_iterations(self):
        """Benchmark with 0 iterations returns empty result."""
        provider = _BenchmarkProvider()
        benchmark = LLMBenchmark(provider)
        request = LLMRequest(user_prompt="test")

        result = await benchmark.run(request, iterations=0, collect_memory=False)
        assert result.iterations == 0
        assert len(result.individual) == 0

    @pytest.mark.asyncio
    async def test_benchmark_empty_response(self):
        """Benchmark handles empty responses gracefully."""
        provider = _NoMemProviderResponses()
        benchmark = LLMBenchmark(provider)
        request = LLMRequest(user_prompt="test")

        result = await benchmark.run(request, iterations=1, collect_memory=False)
        assert result.iterations == 1
