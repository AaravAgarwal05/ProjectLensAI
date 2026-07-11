"""Citation Engine — extracts structured citations from context chunks."""

from __future__ import annotations

import logging
from typing import Any

from src.ai_core.chat.models import CitationReference
from src.ai_core.context.models import ContextChunk

logger = logging.getLogger(__name__)


class CitationEngine:
    """Transforms ContextChunks into structured CitationReferences.

    The Chat Engine never knows about retrieval internals — it only
    works with the chunks returned by the Context Manager.
    """

    def __init__(self, max_citations: int = 10) -> None:
        self._max_citations = max_citations

    def extract(
        self,
        chunks: list[ContextChunk],
        response_text: str | None = None,
    ) -> list[CitationReference]:
        """Build citation references from context chunks.

        Args:
            chunks: Context chunks returned by the Context Manager.
            response_text: Optional response text for cross-referencing.

        Returns:
            Deduplicated citation references, ranked by score.
        """
        if not chunks:
            return []

        seen: set[str] = set()
        citations: list[CitationReference] = []

        for chunk in sorted(chunks, key=lambda c: c.score, reverse=True):
            key = chunk.chunk_id or chunk.source_id or chunk.source_title or ""
            if key in seen:
                continue
            seen.add(key)

            ref = CitationReference(
                report_id=chunk.source_id or chunk.chunk_id,
                report_title=chunk.source_title or "",
                page_number=chunk.page_number,
                section_name=chunk.section_name or "",
                chunk_id=chunk.chunk_id or "",
                score=chunk.score,
            )
            citations.append(ref)

            if len(citations) >= self._max_citations:
                break

        return citations

    def to_dicts(self, citations: list[CitationReference]) -> list[dict[str, Any]]:
        """Convert citation references to dicts for serialization."""
        return [
            {
                "report_id": c.report_id,
                "report_title": c.report_title,
                "page_number": c.page_number,
                "section_name": c.section_name,
                "chunk_id": c.chunk_id,
                "score": c.score,
            }
            for c in citations
        ]

    def from_dicts(self, dicts: list[dict[str, Any]]) -> list[CitationReference]:
        """Convert dicts back to citation references."""
        return [CitationReference(**d) for d in dicts]
