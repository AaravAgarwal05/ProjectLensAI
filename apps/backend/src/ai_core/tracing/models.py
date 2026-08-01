"""Request trace — per-request stage-level observability data."""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RequestTrace:
    """Structured trace for a single request through the RAG pipeline.

    Carries identity (user/session/prompt/model) plus stage-level timing
    so every request can be replayed, debugged, and correlated with
    evaluation runs.
    """

    # Identity
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    user_id: str = ""
    session_id: str = ""
    prompt_version: str = ""
    prompt_hash: str = ""
    model: str = ""
    provider: str = ""
    cache_hit: bool = False

    # Stage timings (ms)
    rewrite_ms: float = 0.0
    embed_ms: float = 0.0
    vector_search_ms: float = 0.0
    bm25_ms: float = 0.0
    cross_encoder_ms: float = 0.0
    mmr_ms: float = 0.0
    context_ms: float = 0.0
    prompt_build_ms: float = 0.0
    llm_ms: float = 0.0
    save_ms: float = 0.0
    total_ms: float = 0.0

    # Counts
    chunks_retrieved: int = 0
    chunks_cited: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def stages(self) -> dict[str, float]:
        """Return the stage-timing map (ms)."""
        return {
            "rewrite": self.rewrite_ms,
            "embed": self.embed_ms,
            "vector_search": self.vector_search_ms,
            "bm25": self.bm25_ms,
            "cross_encoder": self.cross_encoder_ms,
            "mmr": self.mmr_ms,
            "context": self.context_ms,
            "prompt_build": self.prompt_build_ms,
            "llm": self.llm_ms,
            "save": self.save_ms,
            "total": self.total_ms,
        }

    def counts(self) -> dict[str, int]:
        """Return the count map."""
        return {
            "chunks_retrieved": self.chunks_retrieved,
            "chunks_cited": self.chunks_cited,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }

    def to_dict(self) -> dict:
        """Serialize to a flat dict suitable for JSON persistence."""
        d = asdict(self)
        # Drop the derived fields (rebuilt from stages/counts)
        for k in ("rewrite_ms", "embed_ms", "vector_search_ms", "bm25_ms",
                  "cross_encoder_ms", "mmr_ms", "context_ms", "prompt_build_ms",
                  "llm_ms", "save_ms", "total_ms", "chunks_retrieved", "chunks_cited",
                  "prompt_tokens", "completion_tokens"):
            d.pop(k, None)
        d["stages"] = self.stages()
        d["counts"] = self.counts()
        return d

    def log(self, query: str) -> None:
        """Log the trace breakdown as structured info."""
        logger.info(
            "[TRACE] request=%s user=%s session=%s prompt=%s model=%s provider=%s "
            "total=%dms rewrite=%d embed=%d vec=%d bm25=%d ce=%d mmr=%d "
            "context=%d prompt=%d llm=%d save=%d chunks=%d cited=%d tokens=%d+%d",
            self.request_id, self.user_id[:8], self.session_id[:8],
            self.prompt_version, self.model, self.provider,
            int(self.total_ms), int(self.rewrite_ms), int(self.embed_ms),
            int(self.vector_search_ms), int(self.bm25_ms), int(self.cross_encoder_ms),
            int(self.mmr_ms), int(self.context_ms), int(self.prompt_build_ms),
            int(self.llm_ms), int(self.save_ms),
            self.chunks_retrieved, self.chunks_cited,
            self.prompt_tokens, self.completion_tokens,
        )
