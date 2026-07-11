"""Chat Engine — persistent conversational system over the AI pipeline.

Provides:
- **Chat Models**: ChatSession, ChatMessage, CitationReference, etc.
- **Session Manager**: Create, rename, archive, delete sessions.
- **Message Manager**: Create, edit, delete, paginate messages.
- **Chat Orchestrator**: Full pipeline (retrieval → context → LLM → response).
- **Citation Engine**: Extracts structured citations from context chunks.
- **Streaming Support**: SSE-compatible token streaming with cancellation.
- **Validation**: Input/output validation for chat operations.
- **Benchmark Framework**: Metrics collection for chat operations.
"""

from __future__ import annotations

from src.ai_core.chat.citations import CitationEngine
from src.ai_core.chat.config import ChatConfiguration
from src.ai_core.chat.message_manager import MessageManager
from src.ai_core.chat.models import (
    ChatMessage,
    ChatMetadata,
    ChatSession,
    CitationReference,
    MessageRole,
    SessionStatistics,
)
from src.ai_core.chat.orchestrator import ChatOrchestrator
from src.ai_core.chat.session_manager import SessionManager
from src.ai_core.chat.streaming import ChatStreamingEngine
from src.ai_core.chat.validation import ChatValidationEngine

__all__ = [
    "ChatSession",
    "ChatMessage",
    "MessageRole",
    "CitationReference",
    "ChatMetadata",
    "SessionStatistics",
    "ChatConfiguration",
    "SessionManager",
    "MessageManager",
    "ChatOrchestrator",
    "CitationEngine",
    "ChatStreamingEngine",
    "ChatValidationEngine",
]
