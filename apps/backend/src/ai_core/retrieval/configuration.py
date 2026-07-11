"""Retriever configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrieverConfiguration:
    """Configuration for retrieval providers.

    Attributes:
        retriever: Default retriever name (``"dense"``).
        reranker: Default reranker name (``"none"``).
        embedding_model: Embedding provider name (``"sentence_transformers"``).
        collection: Target collection name (``"default"``).
        top_k: Default top-k (``10``).
        score_threshold: Minimum score (optional).
        include_metadata: Include metadata in results (``True``).
        weights: Hybrid retriever weights (``{"dense": 0.5, "sparse": 0.5}``).
        cross_encoder_model: Model for CrossEncoderReranker (optional).
        extra: Store-specific overrides.
    """

    retriever: str = "dense"
    reranker: str = "none"
    embedding_model: str = "sentence_transformers"
    collection: str = "default"
    top_k: int = 10
    score_threshold: float | None = None
    include_metadata: bool = True
    weights: dict[str, float] = field(default_factory=lambda: {"dense": 0.5, "sparse": 0.5})
    cross_encoder_model: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def default(cls) -> RetrieverConfiguration:
        return cls()

    def merge(self, overrides: dict[str, Any]) -> RetrieverConfiguration:
        merged = {**self.__dict__, **overrides}
        if "weights" in overrides:
            merged["weights"] = {**self.weights, **overrides["weights"]}
        return RetrieverConfiguration(**merged)
