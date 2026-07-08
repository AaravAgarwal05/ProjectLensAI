"""Domain model definitions for the ProjectLens platform."""

from shared.models.analysis import AnalysisResult, Citation
from shared.models.chat import Conversation, Message, Thread
from shared.models.common import APIResponse, ErrorResponse, PaginatedResponse
from shared.models.document import Document, DocumentChunk
from shared.models.processing import (
    DocumentMetadata,
    Page,
    ParsedDocument,
    ProcessingError,
    ProcessingStatistics,
    ProcessingWarning,
)
from shared.models.user import User, UserPreferences

__all__ = [
    "AnalysisResult",
    "APIResponse",
    "Citation",
    "Conversation",
    "Document",
    "DocumentChunk",
    "DocumentMetadata",
    "ErrorResponse",
    "Message",
    "Page",
    "PaginatedResponse",
    "ParsedDocument",
    "ProcessingError",
    "ProcessingStatistics",
    "ProcessingWarning",
    "Thread",
    "User",
    "UserPreferences",
]
