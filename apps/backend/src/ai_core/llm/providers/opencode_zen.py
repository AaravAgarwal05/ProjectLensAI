"""OpenCode Zen LLM provider — calls OpenCode Zen API (OpenAI-compatible).

Uses ``https://opencode.ai/zen/v1/chat/completions`` with a
Bearer-token API key obtained from https://opencode.ai/auth.

Free models available (rate-limited):
- ``deepseek-v4-flash-free``
- ``big-pickle``
"""

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

_DEFAULT_BASE_URL = "https://opencode.ai/zen/v1"
_DEFAULT_MODEL = "deepseek-v4-flash-free"
_CHAT_COMPLETIONS_PATH = "/chat/completions"


class OpenCodeZenProvider(LLMProvider):
    """LLM provider backed by OpenCode Zen (OpenAI-compatible API).

    Requires ``OPENCODE_ZEN_API_KEY`` environment variable to be set.
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
        return "opencode_zen"

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
            self._api_key = get_settings().OPENCODE_ZEN_API_KEY
            if not self._api_key:
                logger.warning(
                    "OPENCODE_ZEN_API_KEY is empty — OpenCode Zen provider will fail at runtime"
                )
        return self._api_key

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Non-streaming generation via OpenAI-compatible chat completions."""
        client = await self._get_client()
        model = request.model_name or self._config.model_name or _DEFAULT_MODEL
        key = self._resolve_key()
        payload = self._build_payload(request, model, stream=False)

        try:
            start = time.monotonic()
            response = await client.post(
                _CHAT_COMPLETIONS_PATH,
                json=payload,
                headers={"Authorization": f"Bearer {key}"},
            )
            elapsed_ms = (time.monotonic() - start) * 1000
        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"OpenCode Zen request timed out after {self._config.timeout}s"
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderNotAvailableError(
                f"OpenCode Zen connection failed: {exc}"
            ) from exc

        if response.status_code != 200:
            err = _parse_error(response)
            raise GenerationError(
                f"OpenCode Zen returned {response.status_code}: {err}"
            )

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
        """Streaming generation via OpenAI-compatible chat completions."""
        client = await self._get_client()
        model = request.model_name or self._config.model_name or _DEFAULT_MODEL
        key = self._resolve_key()
        payload = self._build_payload(request, model, stream=True)

        try:
            async with client.stream(
                "POST",
                _CHAT_COMPLETIONS_PATH,
                json=payload,
                headers={"Authorization": f"Bearer {key}"},
            ) as resp:
                if resp.status_code != 200:
                    err = _parse_error(resp)
                    raise StreamingError(
                        f"OpenCode Zen streaming returned {resp.status_code}: {err}"
                    )

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    event_data = line[6:].strip()
                    if event_data == "[DONE]":
                        yield StreamingChunk(
                            text="", finish_reason="stop", token_count=0
                        )
                        return
                    try:
                        chunk = json.loads(event_data)
                    except json.JSONDecodeError:
                        continue

                    delta = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                    )
                    text = delta.get("content", "")
                    finish = (
                        chunk.get("choices", [{}])[0]
                        .get("finish_reason")
                    )
                    if finish:
                        yield StreamingChunk(
                            text="",
                            finish_reason=finish,
                            token_count=0,
                        )
                        return
                    if text:
                        yield StreamingChunk(
                            text=text,
                            finish_reason=None,
                            token_count=0,
                        )

        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"OpenCode Zen streaming timed out after {self._config.timeout}s"
            ) from exc
        except httpx.RequestError as exc:
            raise StreamingError(
                f"OpenCode Zen streaming connection error: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Health & model checks
    # ------------------------------------------------------------------

    async def check_health(self) -> ProviderHealth:
        """Check OpenCode Zen connectivity by listing models."""
        key = self._resolve_key()
        start = time.monotonic()
        try:
            client = await self._get_client()
            resp = await client.get(
                "/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                return ProviderHealth(
                    healthy=True, model_available=True, latency_ms=elapsed_ms
                )
            return ProviderHealth(
                healthy=False,
                model_available=False,
                error=f"HTTP {resp.status_code}",
            )
        except httpx.RequestError as exc:
            return ProviderHealth(
                healthy=False, model_available=False, error=str(exc)
            )

    async def is_model_available(self, model_name: str) -> bool:
        """Check if *model_name* is available via OpenCode Zen."""
        key = self._resolve_key()
        try:
            client = await self._get_client()
            resp = await client.get(
                "/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            if resp.status_code != 200:
                return False
            models = resp.json().get("data", [])
            return any(m.get("id") == model_name for m in models)
        except httpx.RequestError:
            return False

    async def count_tokens(self, text: str) -> int:
        """Estimate token count via centralized tokenizer."""
        if not text:
            return 0
        from src.ai_core.tokenizer import estimate_tokens
        return estimate_tokens(text)

    # ------------------------------------------------------------------
    # Payload builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_payload(
        request: LLMRequest, model: str, stream: bool
    ) -> dict[str, Any]:
        """Build an OpenAI-compatible chat completions payload."""
        messages: list[dict[str, str]] = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        for msg in request.history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": request.user_prompt})

        return {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }


# --------------------------------------------------------------------------
# Module-level helpers
# --------------------------------------------------------------------------


def _extract_text(data: dict) -> str:
    """Extract concatenated text from an OpenAI-compatible response."""
    choices = data.get("choices", [])
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "")


def _extract_usage(data: dict) -> TokenUsage:
    """Extract token usage from an OpenAI-compatible response."""
    usage = data.get("usage", {}) or {}
    return TokenUsage(
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
    )


def _parse_error(response: httpx.Response) -> str:
    """Extract a human-readable error from a non-200 response."""
    try:
        return response.json().get("error", {}).get("message", response.text)
    except Exception:
        return response.text[:200]
