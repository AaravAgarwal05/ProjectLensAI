"""Cross-encoder reranker — uses a cross-encoder model to re-score chunks.

Requires the ``sentence_transformers`` package with a cross-encoder model.
Optional — falls back to identity if model is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

from src.ai_core.retrieval.models import RetrievedChunk, SearchQuery
from src.ai_core.retrieval.reranking.base import Reranker

logger = logging.getLogger(__name__)


class CrossEncoderReranker(Reranker):
    """Reranker that uses a cross-encoder for pairwise query-chunk scoring.

    Configuration keys (via ``configure``):
        model_name: Cross-encoder model (default ``"cross-encoder/ms-marco-MiniLM-L-6-v2"``).
        device: Torch device (default ``"cpu"``).
        batch_size: Inference batch size (default 32).
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model: Any = None

    @property
    def reranker_name(self) -> str:
        return "cross_encoder"

    async def rerank(
        self,
        query: SearchQuery,
        candidates: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        if not candidates:
            return candidates

        model = await self._get_model()
        if model is None:
            logger.debug("Cross-encoder unavailable, returning candidates unchanged")
            return candidates

        pairs = [(query.text, c.content) for c in candidates]
        try:
            scores = model.predict(pairs, batch_size=self._batch_size).tolist()
        except Exception as exc:
            logger.warning("Cross-encoder scoring failed: %s", exc)
            return candidates

        for chunk, score in zip(candidates, scores, strict=False):
            chunk.score = float(score)

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates

    async def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder as _CrossEncoder

            self._model = _CrossEncoder(self._model_name, device=self._device)
        except Exception as exc:
            logger.warning("Failed to load cross-encoder model: %s", exc)
            self._model = None
        return self._model

    def configure(self, params: dict[str, Any]) -> None:
        if "model_name" in params:
            self._model_name = params["model_name"]
            self._model = None
        if "device" in params:
            self._device = params["device"]
            self._model = None
        if "batch_size" in params:
            self._batch_size = int(params["batch_size"])
