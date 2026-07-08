"""Heading-aware chunker — preserves document section hierarchy.

This is the **default** chunking strategy for ProjectLens AI.

The chunker:
1. Parses the document into a heading tree (chapter → section → subsection).
2. Chunks each leaf section independently.
3. Preserves heading context in every chunk's metadata.
4. Maintains page references via character offset tracking.
5. Inherits document-level metadata (title, author, language).

Engineering reports naturally map into this chunking structure.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from shared.models.processing import ParsedDocument

from src.ai_core.chunking.base import ChunkingStrategy
from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.models import Chunk, ChunkingResult, ChunkMetadata

logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# ── Heading detection ─────────────────────────────────────────────

# Matches common heading patterns in engineering reports
_HEADING_RE = re.compile(
    r"^(?:"
    r"#{1,6}\s+|"                             # Markdown-style
    r"(?:CHAPTER|Chapter|chapter)\s+\d+[\s\.:]*|"  # Chapter N
    r"(?:SECTION|Section|section)\s+\d+[\s\.:]*|"  # Section N
    r"\d+\.\d+(?:\.\d+)*\s+|"                # 1.2 or 1.2.3 style
    r"\d+\s*\.\s+|"                          # 1. or 2. style
    r"[A-Z]\s*\.\s+"                         # A. or B. style (appendix)
    r")",
    re.MULTILINE,
)

# Regex to extract heading level from match
_CHAPTER_RE = re.compile(r"(?:CHAPTER|Chapter|chapter)\s+(\d+)", re.IGNORECASE)
_SECTION_NUM_RE = re.compile(r"(\d+(?:\.\d+)*)", re.IGNORECASE)


@dataclass
class _HeadingNode:
    """Internal node in the heading tree."""

    level: int  # 0 = root, 1 = chapter, 2 = section, 3 = subsection, etc.
    title: str  # Full heading text (e.g. "Chapter 1: Introduction")
    start_offset: int
    end_offset: int = 0
    children: list[_HeadingNode] = field(default_factory=list)
    parent: _HeadingNode | None = None


class HeadingAwareChunker(ChunkingStrategy):
    """Chunks documents by detecting and preserving heading hierarchy.

    This is the **default** chunking strategy.  It maps naturally to
    the structure of engineering reports, white papers, and technical
    documentation.
    """

    def __init__(
        self,
        config: ChunkingConfiguration | None = None,
    ) -> None:
        self._config = config or ChunkingConfiguration.default()
        self._name = "heading_aware"

    # ------------------------------------------------------------------
    # ChunkingStrategy interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    def configure(self, params: dict[str, Any]) -> None:
        self._config = self._config.merge(params)

    def validate(self, document: ParsedDocument) -> list[str]:
        warnings: list[str] = []
        if not document.clean_text:
            warnings.append("Document has no clean_text content")
        if not document.pages:
            warnings.append("Document has no page structure — page references unavailable")
        return warnings

    def chunk(self, document: ParsedDocument) -> ChunkingResult:
        warnings = self.validate(document)
        text = document.clean_text

        if not text:
            return ChunkingResult(
                chunks=[],
                warnings=warnings,
                errors=["empty document"],
                successful=False,
            )

        cfg = self._config

        # 1. Build heading tree
        root = self._build_heading_tree(text, cfg.heading_pattern)

        # 2. Walk the tree and chunk each leaf section
        chunks: list[Chunk] = []
        section_path: list[str] = []

        self._chunk_node(
            node=root,
            document=document,
            text=text,
            config=cfg,
            section_path=section_path,
            chunks=chunks,
        )

        result = ChunkingResult(chunks=chunks, warnings=warnings)
        sizes = [len(c.text) for c in chunks]
        token_counts = [c.token_count for c in chunks]
        n = len(chunks)
        result.statistics.number_of_chunks = n
        result.statistics.source = self._name
        if n > 0:
            result.statistics.average_chunk_size = sum(sizes) / n
            result.statistics.average_tokens_per_chunk = sum(token_counts) / n
            result.statistics.largest_chunk = max(sizes)
            result.statistics.smallest_chunk = min(sizes)
        return result

    # ------------------------------------------------------------------
    # Heading tree construction
    # ------------------------------------------------------------------

    def _build_heading_tree(
        self,
        text: str,
        heading_pattern: str,
    ) -> _HeadingNode:
        """Parse *text* into a heading hierarchy.

        Returns the root node.  The root contains all top-level
        headings as children.
        """
        root = _HeadingNode(level=0, title="(root)", start_offset=0, end_offset=len(text))

        # Find all heading matches
        pattern = re.compile(heading_pattern, re.MULTILINE)
        matches = list(pattern.finditer(text))

        if not matches:
            # No headings found — treat whole document as one section
            node = _HeadingNode(level=1, title="(document)", start_offset=0, end_offset=len(text))
            root.children.append(node)
            node.parent = root
            return root

        # Convert matches to nodes and build tree
        nodes: list[_HeadingNode] = []
        for m in matches:
            level = self._detect_heading_level(m.group())
            title = m.group().strip()
            node = _HeadingNode(level=level, title=title, start_offset=m.start())
            nodes.append(node)

        # Assign end offsets
        for i, node in enumerate(nodes):
            if i + 1 < len(nodes):
                node.end_offset = nodes[i + 1].start_offset
            else:
                node.end_offset = len(text)

        # Build tree topology
        for node in nodes:
            self._insert_node(root, node)

        return root

    @staticmethod
    def _detect_heading_level(heading_text: str) -> int:
        """Detect heading level from text.

        Returns:
            1 for Chapter / title-level headings.
            2 for Section / 1.2-style headings.
            3 for Subsection / 1.2.3-style headings.
            4+ for deeper nesting.
        """
        # Markdown style: # is level 1, ## is level 2, etc.
        md_match = re.match(r"^(#+)\s", heading_text)
        if md_match:
            return len(md_match.group(1))

        # Chapter heading → level 1
        if _CHAPTER_RE.match(heading_text):
            return 1

        # Numbered: 1.2.3.4 → level 4
        num_match = _SECTION_NUM_RE.match(heading_text)
        if num_match:
            parts = num_match.group(1).split(".")
            return len(parts)  # "1" → 1, "1.2" → 2, "1.2.3" → 3

        # A. B. style appendix → level 1
        if re.match(r"^[A-Z]\s*\.\s", heading_text):
            return 1

        return 2  # default to section level

    @staticmethod
    def _insert_node(root: _HeadingNode, node: _HeadingNode) -> None:
        """Insert *node* into the correct place in the tree."""
        if not root.children:
            root.children.append(node)
            node.parent = root
            return

        # Walk backwards from the last child to find proper parent
        last = root.children[-1]
        if node.level <= last.level:
            # Sibling: add to root
            root.children.append(node)
            node.parent = root
        else:
            # Child: insert under last sibling
            # Walk down the last sibling's children chain
            parent = last
            while parent.children and node.level > parent.children[-1].level:
                parent = parent.children[-1]
            parent.children.append(node)
            node.parent = parent

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _chunk_node(
        self,
        node: _HeadingNode,
        document: ParsedDocument,
        text: str,
        config: ChunkingConfiguration,
        section_path: list[str],
        chunks: list[Chunk],
    ) -> None:
        """Recursively chunk a heading node and its children."""
        if node.title != "(root)":
            section_path.append(node.title)

        if node.children:
            # Internal node: recurse into children
            for child in node.children:
                self._chunk_node(
                    node=child,
                    document=document,
                    text=text,
                    config=config,
                    section_path=section_path,
                    chunks=chunks,
                )
        else:
            # Leaf node: chunk this section's content
            section_text = text[node.start_offset : node.end_offset].strip()
            if not section_text:
                section_path.pop()
                return

            heading = section_path[-1] if section_path else None
            section = " > ".join(section_path) if section_path else None

            if len(section_text) <= config.chunk_size:
                # Single chunk for this section
                self._append_chunk(
                    text=section_text,
                    document=document,
                    start_offset=node.start_offset,
                    end_offset=node.end_offset,
                    section=section,
                    heading=heading,
                    source=self._name,
                    chunks=chunks,
                )
            else:
                # Split large section into sub-chunks
                self._split_section(
                    text=section_text,
                    document=document,
                    base_offset=node.start_offset,
                    section=section,
                    heading=heading,
                    config=config,
                    chunks=chunks,
                )

        if node.title != "(root)":
            section_path.pop()

    def _split_section(
        self,
        text: str,
        document: ParsedDocument,
        base_offset: int,
        section: str | None,
        heading: str | None,
        config: ChunkingConfiguration,
        chunks: list[Chunk],
    ) -> None:
        """Split a large section into multiple chunks.

        Uses paragraph boundaries (double newlines) as preferred split
        points, falling back to sentence boundaries, then hard split.
        """
        # Try paragraph split first
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            self._split_paragraphs(
                paragraphs=paragraphs,
                document=document,
                base_offset=base_offset,
                section=section,
                heading=heading,
                config=config,
                chunks=chunks,
            )
            return

        # Fall back to sentence split
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) > 1:
            self._merge_to_chunks(
                segments=sentences,
                document=document,
                base_offset=base_offset,
                section=section,
                heading=heading,
                config=config,
                chunks=chunks,
            )
            return

        # Hard character split
        hard_segments = [
            text[i : i + config.chunk_size]
            for i in range(0, len(text), config.chunk_size)
        ]
        self._merge_to_chunks(
            segments=hard_segments,
            document=document,
            base_offset=base_offset,
            section=section,
            heading=heading,
            config=config,
            chunks=chunks,
        )

    def _split_paragraphs(
        self,
        paragraphs: list[str],
        document: ParsedDocument,
        base_offset: int,
        section: str | None,
        heading: str | None,
        config: ChunkingConfiguration,
        chunks: list[Chunk],
    ) -> None:
        """Group paragraphs into chunks respecting chunk_size."""
        current_chunk: list[str] = []
        current_size = 0

        for para in paragraphs:
            para_len = len(para) + 2  # account for \n\n
            if current_size + para_len > config.chunk_size and current_chunk:
                # Flush current buffer
                combined = "\n\n".join(current_chunk)
                joined_text = "\n\n".join(paragraphs)
                start = base_offset + joined_text.find(combined) if chunks else base_offset
                self._append_chunk(
                    text=combined,
                    document=document,
                    start_offset=max(0, start),
                    end_offset=start + len(combined),
                    section=section,
                    heading=heading,
                    source=self._name,
                    chunks=chunks,
                )
                current_chunk = [para]
                current_size = para_len
            else:
                current_chunk.append(para)
                current_size += para_len

        # Flush remaining
        if current_chunk:
            combined = "\n\n".join(current_chunk)
            self._append_chunk(
                text=combined,
                document=document,
                start_offset=base_offset,
                end_offset=base_offset + len(combined),
                section=section,
                heading=heading,
                source=self._name,
                chunks=chunks,
            )

    def _merge_to_chunks(
        self,
        segments: list[str],
        document: ParsedDocument,
        base_offset: int,
        section: str | None,
        heading: str | None,
        config: ChunkingConfiguration,
        chunks: list[Chunk],
    ) -> None:
        """Merge small segments into chunk_size-sized groups."""
        current: list[str] = []
        current_len = 0

        for seg in segments:
            if current_len + len(seg) > config.chunk_size and current:
                combined = " ".join(current)
                self._append_chunk(
                    text=combined,
                    document=document,
                    start_offset=base_offset,
                    end_offset=base_offset + len(combined),
                    section=section,
                    heading=heading,
                    source=self._name,
                    chunks=chunks,
                )
                current = [seg]
                current_len = len(seg)
            else:
                current.append(seg)
                current_len += len(seg)

        if current:
            combined = " ".join(current)
            self._append_chunk(
                text=combined,
                document=document,
                start_offset=base_offset,
                end_offset=base_offset + len(combined),
                section=section,
                heading=heading,
                source=self._name,
                chunks=chunks,
            )

    # ------------------------------------------------------------------
    # Chunk creation helper
    # ------------------------------------------------------------------

    def _append_chunk(
        self,
        text: str,
        document: ParsedDocument,
        start_offset: int,
        end_offset: int,
        section: str | None,
        heading: str | None,
        source: str,
        chunks: list[Chunk],
    ) -> None:
        """Create a Chunk and append it to *chunks*."""
        page = self._estimate_page(document, start_offset)
        metadata = ChunkMetadata(
            page_number=page,
            section=section,
            heading=heading,
            source=source,
            document_title=document.metadata.title,
            document_author=document.metadata.author,
            language=document.metadata.language,
        )
        chunk = Chunk(
            chunk_index=len(chunks),
            report_id=document.report_id,
            report_version_id=document.version_id,
            start_offset=start_offset,
            end_offset=end_offset,
            text=text.strip(),
            token_count=_estimate_tokens(text),
            page_number=page,
            section=section,
            heading=heading,
            metadata=metadata,
        )
        chunks.append(chunk)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_page(document: ParsedDocument, offset: int) -> int | None:
        if not document.pages:
            return None
        cumulative = 0
        for page in document.pages:
            cumulative += len(page.content)
            if offset < cumulative:
                return page.number  # type: ignore[no-any-return]
        return document.pages[-1].number  # type: ignore[no-any-return]
