"""Ollama LLM provider implementation."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from src.ai_core.llm.base import LLMProvider
from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.exceptions import (
    GenerationError,
    ProviderNotAvailableError,
    StreamingError,
    TimeoutError,
)
from src.ai_core.llm.models import (
    GenerationMetadata,
    LLMRequest,
    LLMResponse,
    ProviderHealth,
    StreamingChunk,
    TokenUsage,
)

logger = logging.getLogger(__name__)

_ROUGH_TOKEN_RATIO = 4  # chars per token for local estimation


class OllamaProvider(LLMProvider):
    """LLM provider backed by a local Ollama instance."""

    def __init__(self, config: LLMConfiguration | None = None) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._config.base_url,
                timeout=self._config.timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Non-streaming generation via Ollama /api/generate."""
        client = await self._get_client()
        model = request.model_name or self._config.model_name
        payload = self._build_payload(request, model, stream=False)

        try:
            start = time.monotonic()
            response = await client.post("/api/generate", json=payload)
            elapsed_ms = (time.monotonic() - start) * 1000
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Ollama request timed out after {self._config.timeout}s") from exc
        except httpx.RequestError as exc:
            raise ProviderNotAvailableError(f"Ollama connection failed: {exc}") from exc

        if response.status_code != 200:
            raise GenerationError(f"Ollama returned status {response.status_code}: {response.text}")

        data = response.json()
        text = data.get("response", "")
        usage = TokenUsage(
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=(data.get("prompt_eval_count", 0) + data.get("eval_count", 0)),
        )

        return LLMResponse(
            text=text,
            metadata=GenerationMetadata(
                model=model,
                provider=self.provider_name,
                timestamp=time.time(),
                latency_ms=elapsed_ms,
                token_usage=usage,
            ),
            citations=list(request.metadata.get("citations", [])),
            successful=True,
        )

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamingChunk]:
        """Streaming generation via Ollama /api/generate with stream=True."""
        client = await self._get_client()
        model = request.model_name or self._config.model_name
        payload = self._build_payload(request, model, stream=True)
        finish_reason: str | None = None

        try:
            async with client.stream("POST", "/api/generate", json=payload) as resp:
                if resp.status_code != 200:
                    raise StreamingError(f"Ollama streaming returned status {resp.status_code}")

                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("Ollama sent invalid JSON: %s", line[:80])
                        continue

                    chunk_text = data.get("response", "")
                    if data.get("done"):
                        finish_reason = "stop"
                        # Final metadata chunk — yield with finish_reason
                        yield StreamingChunk(
                            text="",
                            finish_reason=finish_reason,
                            token_count=data.get("eval_count", 0),
                        )
                        return

                    if chunk_text:
                        yield StreamingChunk(
                            text=chunk_text,
                            finish_reason=None,
                            token_count=0,
                        )

        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Ollama streaming timed out after {self._config.timeout}s") from exc
        except httpx.RequestError as exc:
            raise StreamingError(f"Ollama streaming connection error: {exc}") from exc

    # ------------------------------------------------------------------
    # Health & model checks
    # ------------------------------------------------------------------

    async def check_health(self) -> ProviderHealth:
        """Check Ollama connectivity and model availability."""
        model = self._config.model_name
        start = time.monotonic()

        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            elapsed_ms = (time.monotonic() - start) * 1000
        except httpx.RequestError as exc:
            return ProviderHealth(
                healthy=False,
                model_available=False,
                error=f"Connection failed: {exc}",
            )

        if resp.status_code != 200:
            return ProviderHealth(
                healthy=False,
                model_available=False,
                error=f"Ollama returned status {resp.status_code}",
            )

        data = resp.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        model_available = any(model in m or m.startswith(model) for m in models)

        return ProviderHealth(
            healthy=True,
            model_available=model_available,
            latency_ms=elapsed_ms,
        )

    async def is_model_available(self, model_name: str) -> bool:
        """Check if *model_name* is available on the Ollama server."""
        try:
            health = await self.check_health()
            if not health.healthy:
                return False
            # Re-check against the specific requested model
            client = await self._get_client()
            resp = await client.get("/api/tags")
            if resp.status_code != 200:
                return False
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return any(model_name in m or m.startswith(model_name) for m in models)
        except httpx.RequestError:
            return False

    async def count_tokens(self, text: str) -> int:
        """Estimate token count.  Ollama lacks a dedicated count endpoint."""
        if not text:
            return 0
        # Rough local estimate
        return max(1, len(text) // _ROUGH_TOKEN_RATIO)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_payload(self, request: LLMRequest, model: str, stream: bool) -> dict[str, Any]:
        """Build the JSON payload for /api/generate."""
        payload: dict[str, Any] = {
            "model": model,
            "prompt": request.user_prompt,
            "system": request.system_prompt,
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens,
            },
        }
        return payload
