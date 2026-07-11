"""Chunk selection and optimization strategies."""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any

from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import ContextChunk

logger = logging.getLogger(__name__)


class ChunkSelectionStrategy:
    """Sorts, deduplicates, merges, and optimises chunks for context assembly."""

    def __init__(self, config: ContextConfiguration | None = None) -> None:
        self._config = config or ContextConfiguration.default()

    def configure(self, params: dict[str, Any]) -> None:
        self._config = self._config.merge(params)

    def select(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        """Full selection pipeline: sort → dedup → merge → trim."""
        if not chunks:
            return chunks

        selected = self._sort_by_relevance(chunks)
        if self._config.enable_chunk_dedup:
            selected = self._remove_duplicates(selected)
        if self._config.enable_chunk_merging:
            selected = self._merge_adjacent(selected)
        if self._config.enable_parent_expansion:
            selected = self._expand_parent_child(selected)
        selected = self._preserve_citations(selected)
        selected = selected[: self._config.max_chunks]
        return selected

    def _sort_by_relevance(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        return sorted(chunks, key=lambda c: c.score, reverse=True)

    def _remove_duplicates(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        seen: set[str] = set()
        deduped: list[ContextChunk] = []
        for c in chunks:
            key = c.chunk_id or c.content[:80]
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        return deduped

    def _merge_adjacent(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        """Merge consecutive chunks from same source and section."""
        if not chunks:
            return chunks
        merged: list[ContextChunk] = []
        current = chunks[0]
        for next_c in chunks[1:]:
            if (
                current.source_id
                and current.source_id == next_c.source_id
                and current.section_name == next_c.section_name
                and current.source_title == next_c.source_title
            ):
                current = ContextChunk(
                    chunk_id=current.chunk_id,
                    content=current.content + "\n" + next_c.content,
                    score=max(current.score, next_c.score),
                    source_id=current.source_id,
                    source_title=current.source_title,
                    source_version=current.source_version or next_c.source_version,
                    page_number=current.page_number or next_c.page_number,
                    section_name=current.section_name,
                    token_count=current.token_count + next_c.token_count,
                    citations=list(OrderedDict.fromkeys(current.citations + next_c.citations)),
                    metadata={**current.metadata, **next_c.metadata},
                )
            else:
                merged.append(current)
                current = next_c
        merged.append(current)
        return merged

    def _expand_parent_child(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        """Mark parent-child relationships when a chunk's parent is available."""
        ids = {c.chunk_id for c in chunks}
        expanded: list[ContextChunk] = []
        for c in chunks:
            parent_id = c.metadata.get("parent_chunk_id", "")
            if parent_id and parent_id not in ids:
                c.citations.append(f"parent:{parent_id}")
            expanded.append(c)
        return expanded

    def _preserve_citations(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        """Ensure all chunks with scores > 0 have at least source_id as citation."""
        for c in chunks:
            if c.score > 0 and c.source_id and not c.citations:
                c.citations.append(c.source_id)
        return chunks
