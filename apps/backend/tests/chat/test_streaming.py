"""Tests for ChatStreamingEngine."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import pytest

from src.ai_core.chat.streaming import ChatStreamingEngine
from src.ai_core.llm.models import StreamingChunk


class TestChatStreamingEngine:
    def setup_method(self):
        self.engine = ChatStreamingEngine()

    # -- Token streaming --

    @pytest.mark.asyncio
    async def test_stream_tokens_basic(self):
        async def token_gen() -> AsyncIterator[StreamingChunk]:
            yield StreamingChunk(text="Hello")
            yield StreamingChunk(text=" world")
            yield StreamingChunk(text="", finish_reason="stop")

        stream_id = "test-1"
        self.engine.create_cancel_event(stream_id)
        events = []
        async for event in self.engine.stream_tokens(token_gen(), stream_id):
            events.append(event)

        assert len(events) == 3
        # First event: token
        data1 = json.loads(events[0].replace("data: ", "").strip())
        assert data1["type"] == "token"
        assert data1["text"] == "Hello"
        # Second event: token
        data2 = json.loads(events[1].replace("data: ", "").strip())
        assert data2["type"] == "token"
        assert data2["text"] == " world"
        # Third event: done
        data3 = json.loads(events[2].replace("data: ", "").strip())
        assert data3["type"] == "done"
        assert data3["reason"] == "stop"

    @pytest.mark.asyncio
    async def test_stream_tokens_cancelled(self):
        async def token_gen() -> AsyncIterator[StreamingChunk]:
            yield StreamingChunk(text="Partial")
            # Simulate cancellation before next yield
            yield StreamingChunk(text="", finish_reason="cancelled")

        stream_id = "test-cancel"
        self.engine.create_cancel_event(stream_id)
        # Cancel immediately
        self.engine.cancel_stream(stream_id)

        events = []
        async for event in self.engine.stream_tokens(token_gen(), stream_id):
            events.append(event)

        assert len(events) == 1
        data = json.loads(events[0].replace("data: ", "").strip())
        assert data["type"] == "cancelled"

    @pytest.mark.asyncio
    async def test_stream_tokens_error(self):
        async def token_gen() -> AsyncIterator[StreamingChunk]:
            yield StreamingChunk(text="Before error")
            raise RuntimeError("Stream failure")

        stream_id = "test-error"
        self.engine.create_cancel_event(stream_id)
        events = []
        async for event in self.engine.stream_tokens(token_gen(), stream_id):
            events.append(event)

        assert len(events) == 2
        data1 = json.loads(events[0].replace("data: ", "").strip())
        assert data1["type"] == "token"
        data2 = json.loads(events[1].replace("data: ", "").strip())
        assert data2["type"] == "error"
        assert "Stream failure" in data2["message"]

    @pytest.mark.asyncio
    async def test_stream_tokens_cleanup_on_done(self):
        async def token_gen() -> AsyncIterator[StreamingChunk]:
            yield StreamingChunk(text="", finish_reason="stop")

        stream_id = "test-cleanup"
        self.engine.create_cancel_event(stream_id)
        async for _ in self.engine.stream_tokens(token_gen(), stream_id):
            pass

        # Cancel event should be removed
        assert stream_id not in self.engine._cancel_events

    # -- Cancellation API --

    def test_create_cancel_event(self):
        event = self.engine.create_cancel_event("stream-1")
        assert isinstance(event, asyncio.Event)
        assert event.is_set() is False
        assert "stream-1" in self.engine._cancel_events

    def test_cancel_stream(self):
        self.engine.create_cancel_event("stream-1")
        result = self.engine.cancel_stream("stream-1")
        assert result is True
        assert self.engine._cancel_events["stream-1"].is_set()

    def test_cancel_nonexistent_stream(self):
        result = self.engine.cancel_stream("nonexistent")
        assert result is False

    def test_remove_cancel_event(self):
        self.engine.create_cancel_event("stream-1")
        self.engine.remove_cancel_event("stream-1")
        assert "stream-1" not in self.engine._cancel_events

    def test_remove_nonexistent_event(self):
        # Should not raise
        self.engine.remove_cancel_event("nonexistent")

    # -- Stream response with citations --

    @pytest.mark.asyncio
    async def test_stream_response_with_citations(self):
        async def token_gen() -> AsyncIterator[StreamingChunk]:
            yield StreamingChunk(text="Answer")
            yield StreamingChunk(text="", finish_reason="stop")

        stream_id = "test-cite"
        self.engine.create_cancel_event(stream_id)
        citations = [{"report_id": "r1", "score": 0.95}]

        events = []
        async for event in self.engine.stream_response(token_gen(), stream_id, citations=citations):
            events.append(event)

        assert len(events) == 3
        data1 = json.loads(events[0].replace("data: ", "").strip())
        assert data1["type"] == "token"
        data2 = json.loads(events[1].replace("data: ", "").strip())
        assert data2["type"] == "done"
        data3 = json.loads(events[2].replace("data: ", "").strip())
        assert data3["type"] == "citations"
        assert data3["citations"][0]["report_id"] == "r1"

    @pytest.mark.asyncio
    async def test_stream_response_no_citations(self):
        async def token_gen() -> AsyncIterator[StreamingChunk]:
            yield StreamingChunk(text="", finish_reason="stop")

        stream_id = "test-nocite"
        self.engine.create_cancel_event(stream_id)

        events = []
        async for event in self.engine.stream_response(token_gen(), stream_id):
            events.append(event)

        assert len(events) == 1
        data = json.loads(events[0].replace("data: ", "").strip())
        assert data["type"] == "done"

    # -- SSE format --

    def test_format_sse(self):
        result = ChatStreamingEngine._format_sse("token", {"text": "Hello"})
        assert result == 'data: {"type": "token", "text": "Hello"}\n\n'
