"""Metadata enrichment for context chunks."""

from __future__ import annotations

import logging
from typing import Any

from src.ai_core.context.models import ContextChunk

logger = logging.getLogger(__name__)


class MetadataEnricher:
    """Enriches chunks with metadata (title, version, page, section, source)."""

    def enrich(
        self,
        chunks: list[ContextChunk],
        extra: dict[str, Any] | None = None,
    ) -> list[ContextChunk]:
        """Attach metadata to each chunk."""
        if not chunks:
            return chunks

        extra = extra or {}
        for chunk in chunks:
            self._enrich_single(chunk, extra)
        return chunks

    def _enrich_single(self, chunk: ContextChunk, extra: dict[str, Any]) -> None:
        """Fill in metadata fields from chunk attributes or extra dict."""
        if not chunk.source_title and "report_title" in extra:
            chunk.source_title = str(extra["report_title"])

        if not chunk.source_version and "report_version" in extra:
            chunk.source_version = str(extra["report_version"])

        if chunk.page_number is None and "page_number" in extra:
            chunk.page_number = int(extra["page_number"])

        if not chunk.section_name and "section_name" in extra:
            chunk.section_name = str(extra["section_name"])

        if not chunk.source_id and "source_id" in extra:
            chunk.source_id = str(extra["source_id"])

        if not chunk.citations and chunk.source_id:
            chunk.citations.append(chunk.source_id)

        for key, value in extra.items():
            if key not in (
                "report_title",
                "report_version",
                "page_number",
                "section_name",
                "source_id",
            ):
                chunk.metadata[key] = value
