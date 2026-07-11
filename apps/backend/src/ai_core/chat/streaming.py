"""Streaming Engine — SSE-compatible token streaming for chat."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from src.ai_core.llm.models import StreamingChunk

logger = logging.getLogger(__name__)


class ChatStreamingEngine:
    """SSE-compatible chat streaming with cancellation support."""

    def __init__(self) -> None:
        self._cancel_events: dict[str, asyncio.Event] = {}

    def create_cancel_event(self, stream_id: str) -> asyncio.Event:
        """Create a cancel event for a stream."""
        event = asyncio.Event()
        self._cancel_events[stream_id] = event
        return event

    def cancel_stream(self, stream_id: str) -> bool:
        """Cancel a stream by ID. Returns True if cancelled."""
        event = self._cancel_events.get(stream_id)
        if event is None:
            return False
        event.set()
        return True

    def remove_cancel_event(self, stream_id: str) -> None:
        """Clean up a cancel event."""
        self._cancel_events.pop(stream_id, None)

    async def stream_tokens(
        self,
        token_generator: AsyncIterator[StreamingChunk],
        stream_id: str,
    ) -> AsyncIterator[str]:
        """Wrap a token generator into SSE-formatted strings.

        Yields:
            SSE-formatted event strings:
              data: {"type": "token", "text": "..."}
              data: {"type": "citation", "citations": [...]}
              data: {"type": "done"}
              data: {"type": "error", "message": "..."}
        """
        cancel_event = self._cancel_events.get(stream_id)
        collected_text: list[str] = []

        try:
            async for chunk in token_generator:
                if cancel_event and cancel_event.is_set():
                    yield self._format_sse("cancelled", {"reason": "user_cancelled"})
                    return

                if chunk.text:
                    collected_text.append(chunk.text)
                    yield self._format_sse("token", {"text": chunk.text})

                if chunk.finish_reason:
                    yield self._format_sse("done", {"reason": chunk.finish_reason})
                    return

        except asyncio.CancelledError:
            yield self._format_sse("cancelled", {"reason": "connection_closed"})
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            yield self._format_sse("error", {"message": str(exc)})
        finally:
            self.remove_cancel_event(stream_id)

    async def stream_response(
        self,
        token_generator: AsyncIterator[StreamingChunk],
        stream_id: str,
        citations: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Stream tokens with optional final citation block.

        Yields:
            SSE events: token chunks, optional citations, and done.
        """
        async for event in self.stream_tokens(token_generator, stream_id):
            yield event
            if '"done"' in event and citations:
                yield self._format_sse("citations", {"citations": citations})

    @staticmethod
    def _format_sse(event_type: str, data: dict[str, Any]) -> str:
        """Format as SSE data line."""
        payload = json.dumps({"type": event_type, **data})
        return f"data: {payload}\n\n"
