"""REST API endpoints for user processing preferences.

Allows authenticated users to read and update their processing strategy
choices (chunking, LLM, retrieval, embedding).
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.database.models.user import DEFAULT_PREFERENCES, User

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class ProcessingPreferences(BaseModel):
    """User's chosen processing strategies."""

    chunking_strategy: str = Field(
        default=DEFAULT_PREFERENCES["chunking_strategy"],
        description="Chunking strategy: fixed, recursive, heading_aware",
    )
    llm_provider: str = Field(
        default=DEFAULT_PREFERENCES["llm_provider"],
        description="LLM provider: ollama, claude, gpt",
    )
    llm_model: str = Field(
        default=DEFAULT_PREFERENCES["llm_model"],
        description="LLM model: gemma3:1b, llama3.2:1b, etc.",
    )
    retrieval_strategy: str = Field(
        default=DEFAULT_PREFERENCES["retrieval_strategy"],
        description="Retrieval strategy: dense, hybrid, multi_query",
    )
    embedding_provider: str = Field(
        default=DEFAULT_PREFERENCES["embedding_provider"],
        description="Embedding provider: sentence_transformer, ollama",
    )


class PreferencesResponse(BaseModel):
    """Response wrapper for processing preferences."""

    preferences: ProcessingPreferences


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/processing-preferences",
    response_model=PreferencesResponse,
)
async def get_processing_preferences(
    user: User = Depends(get_current_user),
) -> PreferencesResponse:
    """Return the current user's processing strategy preferences."""
    prefs = (
        getattr(user, "preferences", None)
        or dict(DEFAULT_PREFERENCES)
    )
    return PreferencesResponse(
        preferences=ProcessingPreferences(**prefs),
    )


@router.put(
    "/processing-preferences",
    response_model=PreferencesResponse,
    status_code=status.HTTP_200_OK,
)
async def update_processing_preferences(
    body: ProcessingPreferences,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PreferencesResponse:
    """Update the current user's processing strategy preferences.

    Accepts a partial body — only the supplied fields are updated;
    omitted fields keep their current value.
    """
    current_prefs = (
        getattr(user, "preferences", None)
        or dict(DEFAULT_PREFERENCES)
    )
    updated_prefs = dict(current_prefs)
    incoming = body.model_dump(exclude_unset=True)
    updated_prefs.update(incoming)

    user.preferences = updated_prefs
    db.add(user)

    return PreferencesResponse(
        preferences=ProcessingPreferences(**updated_prefs),
    )
