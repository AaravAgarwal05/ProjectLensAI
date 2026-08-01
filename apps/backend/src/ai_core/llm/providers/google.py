"""Google Gemini LLM provider — calls Google AI Studio API."""

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
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Default base URL for Google AI Studio API v1beta.
_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GoogleProvider(LLMProvider):
    """LLM provider backed by Google AI Studio (Gemini models).

    Requires ``GOOGLE_API_KEY`` environment variable (or ``.env.local`` file)
    to be set.  Obtain a free API key at
    https://aistudio.google.com/apikey
    """

    def __init__(self, config: LLMConfiguration | None = None) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        self._api_key: str = ""

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "google"

    # ------------------------------------------------------------------
    # HTTP client
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            base_url = self._config.base_url or _DEFAULT_BASE_URL
            self._client = httpx.AsyncClient(
                base_url=base_url,
                timeout=self._config.timeout,
            )
        return self._client

    def _resolve_key(self) -> str:
        """Load the API key from settings (cached on first call)."""
        if not self._api_key:
            self._api_key = get_settings().GOOGLE_API_KEY
            if not self._api_key:
                logger.warning("GOOGLE_API_KEY is empty — Google provider will fail at runtime")
        return self._api_key

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Non-streaming generation via Gemini generateContent API."""
        client = await self._get_client()
        model = request.model_name or self._config.model_name
        key = self._resolve_key()
        # Key goes in a header, not the query string (avoids key leakage via
        # access logs / referrers). Gemini accepts `x-goog-api-key`.
        url = f"/models/{model}:generateContent"
        headers = {"x-goog-api-key": key}
        payload = self._build_payload(request)

        try:
            start = time.monotonic()
            response = await client.post(url, headers=headers, json=payload)
            elapsed_ms = (time.monotonic() - start) * 1000
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Google request timed out after {self._config.timeout}s") from exc
        except httpx.RequestError as exc:
            raise ProviderNotAvailableError(f"Google connection failed: {exc}") from exc

        if response.status_code != 200:
            err = _parse_error(response)
            raise GenerationError(f"Google returned {response.status_code}: {err}")

        data = response.json()
        text = _extract_text(data)
        usage = _extract_usage(data)

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
        """Streaming generation via Gemini streamGenerateContent API (SSE)."""
        client = await self._get_client()
        model = request.model_name or self._config.model_name
        key = self._resolve_key()
        url = f"/models/{model}:streamGenerateContent?alt=sse"
        headers = {"x-goog-api-key": key}
        payload = self._build_payload(request)

        try:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    err = _parse_error(resp)
                    raise StreamingError(f"Google streaming returned {resp.status_code}: {err}")

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    # Accumulate text from all parts in this chunk
                    parts: list[str] = []
                    finish_reason: str | None = None
                    for c in data.get("candidates", []):
                        for p in c.get("content", {}).get("parts", []):
                            parts.append(p.get("text", ""))
                        fr = c.get("finishReason", "")
                        if fr:
                            finish_reason = fr.lower()

                    text = "".join(parts)
                    if finish_reason:
                        yield StreamingChunk(text=text, finish_reason=finish_reason, token_count=0)
                        return
                    if text:
                        yield StreamingChunk(text=text, finish_reason=None, token_count=0)

        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Google streaming timed out after {self._config.timeout}s") from exc
        except httpx.RequestError as exc:
            raise StreamingError(f"Google streaming connection error: {exc}") from exc

    # ------------------------------------------------------------------
    # Health & model checks
    # ------------------------------------------------------------------

    async def check_health(self) -> ProviderHealth:
        """Check Google AI Studio connectivity and model availability."""
        model = self._config.model_name
        key = self._resolve_key()
        start = time.monotonic()
        try:
            client = await self._get_client()
            resp = await client.get(f"/models/{model}?key={key}")
            elapsed_ms = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                return ProviderHealth(healthy=True, model_available=True, latency_ms=elapsed_ms)
            return ProviderHealth(healthy=False, model_available=False, error=f"HTTP {resp.status_code}")
        except httpx.RequestError as exc:
            return ProviderHealth(healthy=False, model_available=False, error=str(exc))

    async def is_model_available(self, model_name: str) -> bool:
        health = await self.check_health()
        return health.model_available

    async def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        from src.ai_core.tokenizer import estimate_tokens
        return estimate_tokens(text)

    # ------------------------------------------------------------------
    # Payload builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_payload(request: LLMRequest) -> dict[str, Any]:
        """Build Gemini API request body from an ``LLMRequest``.

        Gemini uses:
        - ``systemInstruction`` for the system prompt
        - ``contents`` array for conversation history + current user message
        - ``generationConfig`` for sampling parameters
        """
        contents: list[dict[str, Any]] = []

        # Conversation history  (role is "user" or "model")
        for msg in request.history:
            contents.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})

        # Current user message
        contents.append({"role": "user", "parts": [{"text": request.user_prompt}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "topP": request.top_p,
                "maxOutputTokens": request.max_tokens,
            },
        }

        if request.system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}

        return payload


# --------------------------------------------------------------------------
# Module-level helpers (used by tests too)
# --------------------------------------------------------------------------


def _extract_text(data: dict) -> str:
    """Extract concatenated text from a Gemini generateContent response."""
    parts: list[str] = []
    for c in data.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            parts.append(p.get("text", ""))
    return "".join(parts)


def _extract_usage(data: dict) -> TokenUsage:
    """Extract token usage from a Gemini response."""
    meta = data.get("usageMetadata", {})
    return TokenUsage(
        prompt_tokens=meta.get("promptTokenCount", 0),
        completion_tokens=meta.get("candidatesTokenCount", 0),
        total_tokens=meta.get("totalTokenCount", 0),
    )


def _parse_error(response: httpx.Response) -> str:
    """Extract a human-readable error from a Gemini error response."""
    try:
        return response.json().get("error", {}).get("message", response.text)
    except Exception:
        return response.text[:200]
