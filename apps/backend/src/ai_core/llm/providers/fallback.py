"""Fallback LLM provider — wraps OllamaProvider with model fallback logic."""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import AsyncIterator

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
    LLMRequest,
    LLMResponse,
    ProviderHealth,
    StreamingChunk,
)
from src.ai_core.llm.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)


class FallbackLLMProvider(LLMProvider):
    """LLM provider that wraps OllamaProvider with model-level fallback.

    Attempts the primary model (from ``request.model_name`` or ``config.model_name``)
    first.  If generation fails, it tries each model in ``config.fallback_models``
    in order, logging which model ultimately succeeds.
    """

    def __init__(self, config: LLMConfiguration | None = None) -> None:
        super().__init__(config)
        self._providers: dict[str, OllamaProvider] = {}

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "fallback"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_provider(self, model: str) -> OllamaProvider:
        """Return a cached (lazy-initialised) OllamaProvider for *model*."""
        if model not in self._providers:
            model_cfg = self._config.merge({"model_name": model})
            self._providers[model] = OllamaProvider(config=model_cfg)
        return self._providers[model]

    def _ordered_models(self, request: LLMRequest) -> list[str]:
        """Return the ordered list of models to try (primary first, then fallbacks)."""
        primary = request.model_name or self._config.model_name
        fallbacks = list(self._config.fallback_models or [])
        # Put primary first, deduplicate fallbacks
        seen = {primary}
        ordered = [primary]
        for m in fallbacks:
            if m not in seen:
                seen.add(m)
                ordered.append(m)
        return ordered

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate non-streaming text, falling back through models on failure."""
        ordered = self._ordered_models(request)
        last_error: Exception | None = None

        for model in ordered:
            try:
                provider = self._get_provider(model)
                req = dataclasses.replace(request, model_name=model)
                response = await provider.generate(req)
                if model != ordered[0]:
                    logger.info(
                        "FallbackLLMProvider: primary '%s' failed, "
                        "succeeded with fallback '%s'",
                        ordered[0],
                        model,
                    )
                return response
            except (
                GenerationError,
                ProviderNotAvailableError,
                TimeoutError,
                httpx.RequestError,
            ) as exc:
                logger.warning(
                    "FallbackLLMProvider: model '%s' failed: %s", model, exc
                )
                last_error = exc
                continue

        raise GenerationError(
            f"All fallback models failed. Last error: {last_error}"
        ) from last_error

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamingChunk]:
        """Generate streaming text, falling back through models on failure."""
        ordered = self._ordered_models(request)
        last_error: Exception | None = None

        for model in ordered:
            try:
                provider = self._get_provider(model)
                req = dataclasses.replace(request, model_name=model)
                if model != ordered[0]:
                    logger.info(
                        "FallbackLLMProvider: primary '%s' failed, "
                        "streaming succeeded with fallback '%s'",
                        ordered[0],
                        model,
                    )
                async for chunk in provider.generate_stream(req):
                    yield chunk
                return
            except (
                StreamingError,
                TimeoutError,
                httpx.RequestError,
            ) as exc:
                logger.warning(
                    "FallbackLLMProvider: streaming model '%s' failed: %s",
                    model,
                    exc,
                )
                last_error = exc
                continue

        raise StreamingError(
            f"All fallback models failed for streaming. Last error: {last_error}"
        ) from last_error

    # ------------------------------------------------------------------
    # Health & model checks
    # ------------------------------------------------------------------

    async def check_health(self) -> ProviderHealth:
        """Return healthy if ANY model is reachable."""
        models = [self._config.model_name] + list(self._config.fallback_models or [])
        for model in models:
            try:
                provider = self._get_provider(model)
                health = await provider.check_health()
                if health.healthy:
                    return health
            except Exception:
                continue
        return ProviderHealth(
            healthy=False,
            error="No LLM models available across all fallback providers",
        )

    async def is_model_available(self, model_name: str) -> bool:
        """Check if *model_name* is available on any fallback provider."""
        provider = self._get_provider(model_name)
        return await provider.is_model_available(model_name)

    async def count_tokens(self, text: str) -> int:
        """Estimate token count using the primary model's provider."""
        provider = self._get_provider(self._config.model_name)
        return await provider.count_tokens(text)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close all cached provider clients."""
        for model, provider in self._providers.items():
            try:
                await provider.close()
            except Exception:
                logger.exception(
                    "FallbackLLMProvider: error closing provider for '%s'", model
                )
        self._providers.clear()
