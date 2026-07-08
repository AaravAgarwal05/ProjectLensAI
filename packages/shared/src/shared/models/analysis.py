"""Pydantic models for analysis results and citations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field
from pydantic.main import BaseModel


class Citation(BaseModel):
    """A source citation attached to an analysis result.

    Attributes:
        id: Optional citation identifier.
        source: Source reference (URL, file path, or document title).
        page: Optional page number within the source.
        text: Cited text excerpt.
        relevance_score: Relevance score between 0.0 and 1.0.
    """

    id: UUID | None = None
    source: str
    page: int | None = None
    text: str
    relevance_score: float = 0.0


class AnalysisResult(BaseModel):
    """The outcome of a document analysis operation.

    Attributes:
        id: Unique analysis result identifier.
        document_id: Identifier of the analysed document.
        analysis_type: Type of analysis performed (e.g. ``"summary"``, ``"qa"``).
        content: Analysis output content.
        citations: List of supporting citations.
        confidence: Confidence score between 0.0 and 1.0.
        created_at: Timestamp of creation.
    """

    model_config = {"frozen": True}

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    analysis_type: str
    content: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime
