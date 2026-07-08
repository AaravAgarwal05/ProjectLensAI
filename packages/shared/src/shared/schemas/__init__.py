"""API request/response schemas for the ProjectLens platform."""

from shared.schemas.analysis import AnalysisRequest, AnalysisResponse
from shared.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from shared.schemas.chat import ChatRequest, ChatResponse, MessageCreate
from shared.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from shared.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "MessageCreate",
    "ChatRequest",
    "ChatResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshRequest",
    "AnalysisRequest",
    "AnalysisResponse",
]
