"""Ollama embedding provider.

Default model: ``nomic-embed-text``

Uses the Ollama REST API for embedding generation.
Supports health check, batch embedding, and model existence checks.
"""

from __future__ import annotations

import logging
from typing import Any, cast

import aiohttp

from src.ai_core.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Embedding provider wrapping the Ollama REST API.

    Configuration:
        model_name: Ollama model tag (default ``"nomic-embed-text"``).
        base_url: Ollama server URL (default ``"http://localhost:11434"``).
        timeout: HTTP request timeout in seconds (default 60).
    """

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        timeout: int = 60,
    ) -> None:
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._dimensions: int | None = None

    # ------------------------------------------------------------------
    # EmbeddingProvider interface
    # ------------------------------------------------------------------

    @property
    def dimensions(self) -> int:
        if self._dimensions is None:
            # Probe dimensions by embedding a single token
            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Can't run sync in async context — return conservative default
                return 768  # nomic-embed-text default
            return asyncio.run(self._probe_dimensions())
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def health_check(self) -> bool:
        """Check whether the Ollama server is reachable."""
        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self._timeout)
                ) as session,
                session.get(f"{self._base_url}/api/tags") as resp,
            ):
                return resp.status == 200
        except Exception:
            return False

    async def model_exists(self, model_name: str | None = None) -> bool:
        """Check whether *model_name* is available on the Ollama server."""
        name = model_name or self._model_name
        try:
            async with (
                aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self._timeout)
                ) as session,
                session.get(f"{self._base_url}/api/tags") as resp,
            ):
                if resp.status != 200:
                    return False
                data = await resp.json()
                models = data.get("models", [])
                return any(m.get("name", "").startswith(name) for m in models)
        except Exception:
            return False

    async def embed(self, text: str) -> list[float]:
        """Embed a single text via the Ollama API."""
        payload = {
            "model": self._model_name,
            "prompt": text,
        }
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._timeout)) as session,
            session.post(f"{self._base_url}/api/embeddings", json=payload) as resp,
        ):
            if resp.status != 200:
                error_text = await resp.text()
                raise RuntimeError(f"Ollama API error ({resp.status}): {error_text}")
            data = await resp.json()
            vector: list[float] = cast(list[float], data.get("embedding", []))
            if self._dimensions is None and vector:
                self._dimensions = len(vector)
            return vector

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts via the Ollama API.

        Calls ``/api/embed`` with an array of inputs (Ollama 0.1.34+).
        Falls back to sequential ``/api/embeddings`` calls for older versions.
        """
        if not texts:
            return []

        # Try batch endpoint first
        try:
            return await self._batch_embed(texts)
        except Exception:
            logger.debug("Batch embed failed, falling back to sequential")
            results: list[list[float]] = []
            for text in texts:
                results.append(await self.embed(text))
            return results

    async def _batch_embed(self, texts: list[str]) -> list[list[float]]:
        """Use the Ollama ``/api/embed`` batch endpoint."""
        payload = {
            "model": self._model_name,
            "input": texts,
        }
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._timeout)) as session,
            session.post(f"{self._base_url}/api/embed", json=payload) as resp,
        ):
            if resp.status != 200:
                raise RuntimeError(f"Ollama batch API returned {resp.status}")
            data = await resp.json()
            raw_embeddings = cast(list[list[float]], data.get("embeddings", []))
            if self._dimensions is None and raw_embeddings:
                self._dimensions = len(raw_embeddings[0])
            return raw_embeddings

    async def _probe_dimensions(self) -> int:
        """Probe embedding dimensions with a single API call."""
        try:
            result = await self.embed("probe")
            return len(result)
        except Exception:
            return 768  # fallback default

    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure the provider."""
        if "model_name" in params:
            self._model_name = params["model_name"]
            self._dimensions = None
        for key in ("base_url", "timeout"):
            if key in params:
                setattr(self, f"_{key}", params[key])
