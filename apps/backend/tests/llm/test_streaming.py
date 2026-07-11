"""Tests for StreamingEngine."""

from __future__ import annotations

import asyncio

import pytest

from src.ai_core.llm.base import LLMProvider
from src.ai_core.llm.exceptions import StreamingError, TimeoutError
from src.ai_core.llm.models import (
    GenerationMetadata,
    LLMRequest,
    LLMResponse,
    StreamingChunk,
    TokenUsage,
)
from src.ai_core.llm.streaming import StreamingEngine


class _StreamingProvider(LLMProvider):
    """A test provider that simulates streaming."""

    @property
    def provider_name(self) -> str:
        return "test"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            text="Hello world",
            metadata=GenerationMetadata(token_usage=TokenUsage(completion_tokens=2)),
        )

    async def generate_stream(self, request: LLMRequest):
        for char in request.user_prompt:
            yield StreamingChunk(text=char)
        yield StreamingChunk(text="", finish_reason="stop")

    async def check_health(self):
        return None  # pragma: no cover

    async def count_tokens(self, text: str) -> int:
        return 0  # pragma: no cover

    async def is_model_available(self, model_name: str) -> bool:
        return True  # pragma: no cover


class _FailingStreamProvider(LLMProvider):
    """A test provider whose streaming always fails."""

    @property
    def provider_name(self) -> str:
        return "failing"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="Fallback response")

    async def generate_stream(self, request: LLMRequest):
        if False:
            yield  # pragma: no cover -- makes this an async generator
        raise StreamingError("Stream broke")

    async def check_health(self):
        return None  # pragma: no cover

    async def count_tokens(self, text: str) -> int:
        return 0  # pragma: no cover

    async def is_model_available(self, model_name: str) -> bool:
        return True  # pragma: no cover


class TestStreamingEngine:
    @pytest.mark.asyncio
    async def test_stream_basic(self):
        """Test basic streaming collects all tokens."""
        provider = _StreamingProvider()
        engine = StreamingEngine(provider)
        request = LLMRequest(user_prompt="Hi", stream=True)

        chunks = []
        async for chunk in engine.stream(request):
            chunks.append(chunk)

        texts = [c.text for c in chunks if c.text]
        assert "".join(texts) == "Hi"
        assert any(c.finish_reason == "stop" for c in chunks)

    @pytest.mark.asyncio
    async def test_stream_cancellation(self):
        """Test stream cancellation via cancel_event."""
        provider = _StreamingProvider()
        engine = StreamingEngine(provider)
        request = LLMRequest(user_prompt="Hello World", stream=True)
        cancel_event = asyncio.Event()

        chunks = []
        async for chunk in engine.stream(request, cancel_event=cancel_event):
            chunks.append(chunk)
            if len(chunks) >= 2:
                cancel_event.set()

        assert len(chunks) >= 2

    @pytest.mark.asyncio
    async def test_stream_timeout(self):
        """Test stream timeout raises TimeoutError."""

        class _SlowProvider(_StreamingProvider):
            async def generate_stream(self, request: LLMRequest):
                await asyncio.sleep(10)
                yield StreamingChunk(text="x")

        provider = _SlowProvider()
        engine = StreamingEngine(provider)
        request = LLMRequest(user_prompt="test", stream=True)

        with pytest.raises(TimeoutError, match="Stream exceeded timeout"):
            async for _ in engine.stream(request, timeout=0.01):
                pass

    @pytest.mark.asyncio
    async def test_stream_fallback(self):
        """Test fallback to non-streaming when streaming fails."""
        provider = _FailingStreamProvider()
        engine = StreamingEngine(provider)
        request = LLMRequest(user_prompt="test", stream=True)

        chunks = []
        async for chunk in engine.stream_with_fallback(request):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].text == "Fallback response"
        assert chunks[0].finish_reason == "stop"
