"""Chunking configuration — defines parameters for every chunking strategy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChunkingConfiguration:
    """Configuration for chunking strategies.

    Sensible defaults are provided for every parameter.  Individual
    chunkers may ignore parameters they don't need.

    Attributes:
        chunk_size: Target character count per chunk (default: 1000).
        chunk_overlap: Number of overlapping characters between chunks.
        min_chunk_size: Minimum allowed chunk size in characters.
        max_chunk_size: Maximum allowed chunk size in characters.
        separator_priority: Ordered list of separators (most preferred first).
        preserve_paragraphs: Whether to keep paragraphs intact when possible.
        max_chunks: Maximum number of chunks to produce (0 = unlimited).
        heading_pattern: Regex pattern for detecting headings.
        strip_whitespace: Whether to strip leading/trailing whitespace.
        extra: Chunker-specific configuration overrides.
    """

    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    separator_priority: list[str] = field(
        default_factory=lambda: ["\n\n", "\n", ".", " ", ""]
    )
    preserve_paragraphs: bool = True
    max_chunks: int = 0
    heading_pattern: str = r"^(#{1,6}\s+|(?:\d+\.)+(?:\d+\s|\s)|(?:CHAPTER|Chapter|chapter)\s+\d+)"
    strip_whitespace: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def default(cls) -> ChunkingConfiguration:
        """Return a default configuration."""
        return cls()

    def merge(self, overrides: dict[str, Any]) -> ChunkingConfiguration:
        """Return a new configuration with *overrides* applied."""
        merged = {**self.__dict__, **overrides}
        return ChunkingConfiguration(**merged)
