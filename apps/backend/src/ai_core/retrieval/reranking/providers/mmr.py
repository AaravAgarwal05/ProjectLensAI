"""MMR (Maximal Marginal Relevance) reranker — balances relevance with diversity.

Uses embedding similarity between chunks to penalize redundancy, producing
a diverse top-K set.  Works as a final pass after relevance scoring.
"""

from __future__ import annotations

import logging
from typing import Any

from src.ai_core.retrieval.models import RetrievedChunk, SearchQuery
from src.ai_core.retrieval.reranking.base import Reranker

logger = logging.getLogger(__name__)


class MMRReranker(Reranker):
    """Reranker that applies Maximal Marginal Relevance for diversity.

    Configuration keys (via ``configure``):
        lambda_: Trade-off between relevance (1.0) and diversity (0.0).
            Default 0.7 — favours relevance while still diversifying.
        top_k: Number of chunks to keep after MMR selection.
        embedding_similarity_fn: Optional callable(a, b) -> float [0,1]
            for computing chunk pairwise similarity.  Defaults to a simple
            word-overlap heuristic.
    """

    def __init__(
        self,
        lambda_: float = 0.7,
        top_k: int = 5,
        embedding_similarity_fn: Any = None,
    ) -> None:
        self._lambda = lambda_
        self._top_k = top_k
        self._sim_fn = embedding_similarity_fn or self._word_overlap_similarity

    @property
    def reranker_name(self) -> str:
        return "mmr"

    async def rerank(
        self,
        query: SearchQuery,
        candidates: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        if not candidates or len(candidates) <= 1:
            return candidates

        top_k = self._top_k
        if top_k <= 0:
            top_k = len(candidates)

        selected: list[RetrievedChunk] = []
        remaining = list(candidates)

        # First pick: highest relevance
        best = remaining.pop(0)
        selected.append(best)

        while len(selected) < top_k and remaining:
            best_idx = -1
            best_score = -1.0

            for i, cand in enumerate(remaining):
                # Relevance term
                relevance = cand.score

                # Diversity term — max similarity to any already-selected
                max_sim = 0.0
                for sel in selected:
                    sim = self._sim_fn(cand, sel)
                    if sim > max_sim:
                        max_sim = sim

                # MMR score
                mmr_score = self._lambda * relevance - (1 - self._lambda) * max_sim
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            if best_idx < 0:
                break
            selected.append(remaining.pop(best_idx))

        # Preserve original scores in metadata, return mmr-sorted
        for i, c in enumerate(selected):
            if "original_score" not in c.metadata:
                c.metadata["original_score"] = c.score
            c.score = 1.0 - (i / max(len(selected), 1))  # rank-based score

        return selected

    @staticmethod
    def _word_overlap_similarity(a: RetrievedChunk, b: RetrievedChunk) -> float:
        """Simple word-overlap similarity in [0, 1]."""
        words_a = set(a.content.lower().split())
        words_b = set(b.content.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)

    def configure(self, params: dict[str, Any]) -> None:
        if "lambda_" in params or "lambda" in params:
            self._lambda = params.get("lambda_", params.get("lambda", 0.7))
        if "top_k" in params:
            self._top_k = int(params["top_k"])
        if "embedding_similarity_fn" in params:
            self._sim_fn = params["embedding_similarity_fn"]
