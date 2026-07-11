"""Configuration for context assembly pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextConfiguration:
    """Configuration for context assembly."""

    max_tokens: int = 8192
    system_prompt_tokens: int = 500
    max_history_tokens: int = 2048
    max_chunk_tokens: int = 4096
    max_chunks: int = 20
    reserved_tokens: int = 256
    conversation_max_messages: int = 20
    enable_conversation_summary: bool = True
    enable_chunk_dedup: bool = True
    enable_chunk_merging: bool = True
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
