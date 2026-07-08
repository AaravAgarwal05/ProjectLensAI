"""Sentence-Transformers embedding provider.

Default model: ``BAAI/bge-small-en-v1.5``

Supports batch embedding, device configuration, and L2 normalisation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from src.ai_core.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class SentenceTransformerProvider(EmbeddingProvider):
    """Embedding provider wrapping ``sentence-transformers``.

    Configuration:
        model_name: HuggingFace model ID (default ``"BAAI/bge-small-en-v1.5"``).
        device: Torch device (``"cpu"``, ``"cuda"``). Default ``"cpu"``.
        batch_size: Max texts per batch (default 32).
        normalize_embeddings: L2-normalise output vectors (default True).
        cache_folder: Model cache directory (optional).
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        cache_folder: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._normalize = normalize_embeddings
        self._cache_folder = cache_folder
        self._model: SentenceTransformer | None = None

    # ------------------------------------------------------------------
    # Lazy model loading
    # ------------------------------------------------------------------

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-loaded SentenceTransformer model."""
        if self._model is None:
            self._load_model()
        return self._model  # type: ignore[return-value]  # _model set by _load_model

    def _load_model(self) -> None:
        """Load the SentenceTransformer model."""
        from sentence_transformers import SentenceTransformer

        kwargs: dict[str, Any] = {"device": self._device}
        if self._cache_folder:
            kwargs["cache_folder"] = self._cache_folder

        logger.info(
            "Loading SentenceTransformer model '%s' on %s",
            self._model_name,
            self._device,
        )
        loaded = SentenceTransformer(self._model_name, **kwargs)
        self._model = loaded
        dim = loaded.get_embedding_dimension()
        logger.info("Model loaded. Dimensions: %d", dim or 0)

    # ------------------------------------------------------------------
    # EmbeddingProvider interface
    # ------------------------------------------------------------------

    @property
    def dimensions(self) -> int:
        d = self.model.get_embedding_dimension()
        return d if d is not None else 0

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        return "sentence_transformers"

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        embedding = self.model.encode(
            text,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
        )
        if isinstance(embedding, np.ndarray):
            return embedding.tolist()
        if isinstance(embedding, list):
            return embedding
        return list(embedding)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
        )
        if isinstance(embeddings, np.ndarray):
            return [e.tolist() for e in embeddings]
        if isinstance(embeddings, list):
            return embeddings
        return [list(e) for e in embeddings]

    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure the provider."""
        if "device" in params and params["device"] != self._device:
            self._device = params["device"]
            self._model = None  # Force reload on next call
        for key in ("batch_size", "normalize_embeddings", "cache_folder"):
            if key in params:
                setattr(self, f"_{key}", params[key])
        if "model_name" in params and params["model_name"] != self._model_name:
            self._model_name = params["model_name"]
            self._model = None
