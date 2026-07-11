"""Data models for LLM context assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ContextRole(StrEnum):
    """Role of a conversation participant."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContextStrategyType(StrEnum):
    """Supported context assembly strategies."""

    SINGLE_DOCUMENT = "single_document"
    MULTI_DOCUMENT = "multi_document"
    COMPARISON = "comparison"
    SUMMARY = "summary"


@dataclass
class ConversationMessage:
    """A single message in a conversation."""

    role: ContextRole | str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float | None = None


@dataclass
class ConversationSummary:
    """Summarized conversation context."""

    text: str
    token_count: int = 0
    message_count: int = 0


@dataclass
class ContextChunk:
    """A single chunk prepared for LLM context."""

    chunk_id: str
    content: str
    score: float = 0.0
    source_id: str = ""
    source_title: str = ""
    source_version: str = ""
    page_number: int | None = None
    section_name: str = ""
    token_count: int = 0
    citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextBudget:
    """Token budget allocation for sections."""

    total: int = 0
    system_prompt: int = 0
    conversation_history: int = 0
    retrieved_chunks: int = 0
    metadata: int = 0
    user_query: int = 0
    reserved: int = 0

    @property
    def allocated(self) -> int:
        return (
            self.system_prompt
            + self.conversation_history
            + self.retrieved_chunks
            + self.metadata
            + self.user_query
            + self.reserved
        )

    @property
    def remaining(self) -> int:
        return self.total - self.allocated


@dataclass
class ContextMetadata:
    """Metadata about the assembled context."""

    query_text: str = ""
    strategy: str = ""
    num_chunks: int = 0
    num_messages: int = 0
    has_conversation_summary: bool = False
    total_tokens: int = 0
    assembly_time: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ContextStatistics:
    """Benchmark statistics for context assembly."""

    context_size: int = 0
    token_usage: int = 0
    assembly_latency: float = 0.0
    history_utilization: float = 0.0
    retrieval_utilization: float = 0.0


@dataclass
class LLMContext:
    """Final assembled context ready for LLM consumption."""

    query: str = ""
    system_prompt: str = ""
    chunks: list[ContextChunk] = field(default_factory=list)
    conversation_history: list[ConversationMessage] = field(default_factory=list)
    conversation_summary: ConversationSummary | None = None
    budget: ContextBudget = field(default_factory=ContextBudget)
    metadata: ContextMetadata = field(default_factory=ContextMetadata)
    statistics: ContextStatistics = field(default_factory=ContextStatistics)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    successful: bool = True

    @property
    def full_text(self) -> str:
        """Render context as flat text for LLM ingestion."""
        parts: list[str] = []
        if self.system_prompt:
            parts.append(self.system_prompt)
        if self.query:
            parts.append(f"Query: {self.query}")
        if self.conversation_summary:
            parts.append(f"Conversation Summary: {self.conversation_summary.text}")
        for msg in self.conversation_history:
            parts.append(f"{msg.role}: {msg.content}")
        for i, chunk in enumerate(self.chunks):
            header = f"Chunk {i + 1}"
            if chunk.section_name:
                header += f" [{chunk.section_name}]"
            if chunk.page_number is not None:
                header += f" (p. {chunk.page_number})"
            parts.append(f"{header}: {chunk.content}")
        return "\n\n".join(parts)
