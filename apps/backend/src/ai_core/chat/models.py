"""Data models for the Chat Engine."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class MessageRole(StrEnum):
    """Role of a chat message."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class CitationReference:
    """A citation linking a response to a source document chunk."""

    report_id: str = ""
    report_title: str = ""
    page_number: int | None = None
    section_name: str = ""
    chunk_id: str = ""
    score: float = 0.0


@dataclass
class ChatMetadata:
    """Aggregated metadata about the chat system."""

    total_sessions: int = 0
    total_messages: int = 0
    active_sessions: int = 0


@dataclass
class SessionStatistics:
    """Statistics for a single chat session."""

    message_count: int = 0
    token_count: int = 0
    citation_count: int = 0
    average_response_time: float = 0.0


@dataclass
class ChatSession:
    """A persistent chat session."""

    id: str = ""
    title: str = ""
    report_ids: list[str] = field(default_factory=list)
    mode: str = "single"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived: bool = False

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())


@dataclass
class ChatMessage:
    """A single message in a chat session."""

    id: str = ""
    session_id: str = ""
    role: str = MessageRole.USER
    content: str = ""
    citations: list[CitationReference] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())
