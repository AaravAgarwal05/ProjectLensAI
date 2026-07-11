"""Chat configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ChatConfiguration:
    """Configuration for the Chat Engine."""

    default_mode: str = "single"
    max_history_messages: int = 50
    enable_streaming: bool = True
    enable_citations: bool = True
    enable_persistence: bool = True
    enable_benchmark: bool = False

    max_message_length: int = 10000
    max_citations_per_response: int = 10

    retrieval_top_k: int = 10
    retrieval_min_score: float = 0.0

    system_prompt: str = (
        "You are a helpful AI assistant for ProjectLens AI. "
        "Answer questions based on the provided context. "
        "When referencing information from a document, include the "
        "source citation."
    )

    def merge(self, params: dict[str, Any]) -> ChatConfiguration:
        d = self.to_dict()
        d.update(params)
        return ChatConfiguration(**d)

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_mode": self.default_mode,
            "max_history_messages": self.max_history_messages,
            "enable_streaming": self.enable_streaming,
            "enable_citations": self.enable_citations,
            "enable_persistence": self.enable_persistence,
            "enable_benchmark": self.enable_benchmark,
            "max_message_length": self.max_message_length,
            "max_citations_per_response": self.max_citations_per_response,
            "retrieval_top_k": self.retrieval_top_k,
            "retrieval_min_score": self.retrieval_min_score,
            "system_prompt": self.system_prompt,
        }
