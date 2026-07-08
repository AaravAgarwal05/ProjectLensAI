"""Event type enumeration for the platform event bus."""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """Canonical event types emitted by platform components."""

    # Document lifecycle
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_FAILED = "document.failed"

    # Chunk / embedding
    CHUNK_CREATED = "chunk.created"
    EMBEDDING_CREATED = "embedding.created"

    # Query lifecycle
    QUERY_EXECUTED = "query.executed"
    QUERY_COMPLETED = "query.completed"

    # Authentication
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"

    # Analysis
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_COMPLETED = "analysis.completed"

    # Conversation
    CONVERSATION_CREATED = "conversation.created"
    MESSAGE_SENT = "message.sent"

    # System
    ERROR_OCCURRED = "error.occurred"
