"""Configuration for context assembly pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextConfiguration:
    """Configuration for context assembly."""

    max_tokens: int = 8192
    system_prompt_tokens: int = 150
    max_history_tokens: int = 1024
    max_chunk_tokens: int = 6144
    max_chunks: int = 15
    reserved_tokens: int = 256
    conversation_max_messages: int = 20
    enable_conversation_summary: bool = True
    enable_chunk_dedup: bool = True
    # Merging is OFF by default: _merge_adjacent assumes input is in document
    # order, but retrieval feeds chunks ranked by relevance/MMR, so it re-glues
    # non-contiguous same-section chunks into one blob and collapses per-chunk
    # citations (retrieved=4, cited=1). Re-enable only with real adjacency info.
    enable_chunk_merging: bool = False
    enable_parent_expansion: bool = True
    default_strategy: str = "single_document"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def default(cls) -> ContextConfiguration:
        return cls()

    def merge(self, overrides: dict[str, Any]) -> ContextConfiguration:
        """Return new config with overrides applied."""
        merged = ContextConfiguration(**{**self.__dict__, **overrides})
        return merged

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}
