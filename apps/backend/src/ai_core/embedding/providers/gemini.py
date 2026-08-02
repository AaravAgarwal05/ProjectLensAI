"""Google Gemini embedding provider.

Default model: ``text-embedding-004`` (768-dim, free Google AI Studio tier).

Uses the Gemini ``embedContent`` / ``batchEmbedContents`` REST API, mirroring
the GoogleProvider LLM client pattern (httpx, ``x-goog-api-key`` header).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.ai_core.embedding.base import EmbeddingProvider
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_DEFAULT_MODEL = "text-embedding-004"
_DEFAULT_DIMENSIONS = 768  # text-embedding-004 output dimension
_BATCH_LIMIT = 100  # Gemini caps batchEmbedContents at 100 requests per call


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by Google Gemini (text-embedding-004).

    Configuration:
        model_name: Gemini embedding model id (default ``"text-embedding-004"``).
        base_url: API base URL (default Google AI Studio v1beta).
        timeout: HTTP timeout in seconds (default 60).
        api_key: Optional override; falls back to ``GOOGLE_API_KEY``.
    """

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: int = 60,
        api_key: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._api_key = api_key or ""
        self._dimensions = _DEFAULT_DIMENSIONS
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # EmbeddingProvider interface
    # ------------------------------------------------------------------

    @property
    def dimensions(self) -> int:
        # Static default for text-embedding-004; updated from the first
        # real response if a different model (e.g. gemini-embedding-001)
        # is configured. Never probes the network synchronously.
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def health_check(self) -> bool:
        """Check model availability via the Gemini models endpoint."""
        try:
            client = await self._get_client()
            resp = await client.get(f"/models/{self._model_name}")
            return resp.status_code == 200
        except Exception:
            return False

    async def embed(self, text: str) -> list[float]:
        """Embed a single text via the Gemini ``embedContent`` API."""
        payload = {
            "model": f"models/{self._model_name}",
            "content": {"parts": [{"text": text}]},
        }
        data = await self._post(f"/models/{self._model_name}:embedContent", payload)
        values = data.get("embedding", {}).get("values", [])
        vector = [float(v) for v in values]
        if vector:
            self._dimensions = len(vector)
        return self._normalize(vector)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch via ``batchEmbedContents`` (chunked at 100)."""
        if not texts:
            return []

        vectors: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_LIMIT):
            batch = texts[i : i + _BATCH_LIMIT]
            payload = {
                "requests": [
                    {
                        "model": f"models/{self._model_name}",
                        "content": {"parts": [{"text": text}]},
                    }
                    for text in batch
                ]
            }
            data = await self._post(
                f"/models/{self._model_name}:batchEmbedContents", payload
            )
            for embedding in data.get("embeddings", []):
                values = embedding.get("values", [])
                vector = [float(v) for v in values]
                if vector:
                    self._dimensions = len(vector)
                vectors.append(self._normalize(vector))
        return vectors

    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure the provider."""
        if "model_name" in params:
            self._model_name = params["model_name"]
            self._dimensions = _DEFAULT_DIMENSIONS
        if "base_url" in params:
            self._base_url = params["base_url"].rstrip("/")
            self._client = None  # force client rebuild on new base URL
        for key in ("timeout", "api_key"):
            if key in params:
                setattr(self, f"_{key}", params[key])

    # ------------------------------------------------------------------
    # HTTP client
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            key = self._api_key or get_settings().GOOGLE_API_KEY
            if not key:
                logger.warning("GOOGLE_API_KEY is empty — Gemini embeddings will fail at runtime")
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={"x-goog-api-key": key},
            )
        return self._client

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            raise RuntimeError(
                f"Gemini embedding API error ({response.status_code}): {self._error(response)}"
            )
        return response.json()

    @staticmethod
    def _error(response: httpx.Response) -> str:
        try:
            return response.json().get("error", {}).get("message", response.text)
        except Exception:
            return response.text[:200]

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        """L2-normalize a vector.

        Gemini returns unit vectors already, so this is a safety no-op that
        keeps output consistent with the other providers (cosine == dot).
        """
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 1e-12:
            return [v / norm for v in vector]
        return vector
