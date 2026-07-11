"""Streaming Engine — wraps provider streaming with safety features."""

from __future__ import annotations

import asyncio
import builtins
import logging
from collections.abc import AsyncIterator

from src.ai_core.llm.base import LLMProvider
from src.ai_core.llm.exceptions import StreamingError, TimeoutError
from src.ai_core.llm.models import (
    LLMRequest,
    StreamingChunk,
)

logger = logging.getLogger(__name__)


class StreamingEngine:
    """Wrapper around LLM provider streaming with cancellation, timeout,
    and graceful fallback to non-streaming."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def stream(
        self,
        request: LLMRequest,
        timeout: float | None = None,
        cancel_event: asyncio.Event | None = None,
    ) -> AsyncIterator[StreamingChunk]:
        """Stream tokens from the provider, handling timeout and cancellation.

        Args:
            request: The generation request (stream flag will be forced True).
            timeout: Max seconds for the entire stream (default: provider config).
            cancel_event: When set, stops streaming gracefully.

        Yields:
            StreamingChunks as tokens arrive.
        """
        if cancel_event is None:
            cancel_event = asyncio.Event()

        effective_timeout = timeout or self._provider._config.stream_timeout  # noqa: SLF001

        request.stream = True
        chunk_count = 0

        try:
            async with asyncio.timeout(effective_timeout):
                async for chunk in self._provider.generate_stream(request):
                    if cancel_event.is_set():
                        logger.info("Stream cancelled by caller after %d chunks", chunk_count)
                        yield StreamingChunk(
                            text="",
                            finish_reason="cancelled",
                        )
                        return

                    if chunk.finish_reason:
                        yield chunk
                        return

                    chunk_count += 1
                    yield chunk

        except builtins.TimeoutError as exc:
            raise TimeoutError(f"Stream exceeded timeout of {effective_timeout}s") from exc
        except StreamingError:
            raise
        except Exception as exc:
            raise StreamingError(f"Stream failed unexpectedly: {exc}") from exc

    async def stream_with_fallback(
        self,
        request: LLMRequest,
        timeout: float | None = None,
        cancel_event: asyncio.Event | None = None,
    ) -> AsyncIterator[StreamingChunk]:
        """Attempt streaming; fall back to non-streaming on failure.

        If streaming fails, the entire response is yielded as a single chunk.
        """
        try:
            async for chunk in self.stream(request, timeout, cancel_event):
                yield chunk
        except (StreamingError, TimeoutError) as exc:
            logger.warning("Stream failed, falling back to non-streaming: %s", exc)
            request.stream = False
            response = await self._provider.generate(request)
            total = response.metadata.token_usage.completion_tokens
            yield StreamingChunk(
                text=response.text,
                finish_reason="stop",
                token_count=total,
            )
