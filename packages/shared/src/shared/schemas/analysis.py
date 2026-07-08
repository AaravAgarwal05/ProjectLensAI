"""API schemas for document analysis requests and responses."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field
from pydantic.main import BaseModel

from shared.models.analysis import AnalysisResult


class AnalysisRequest(BaseModel):
    """Request schema for triggering a document analysis.

    Attributes:
        document_id: Identifier of the document to analyse.
        analysis_type: Type of analysis (e.g. ``"summary"``, ``"qa"``).
        options: Optional configuration key-value pairs for the analysis.
    """

    document_id: UUID
    analysis_type: str
    options: dict = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    """Response schema for a completed analysis.

    Attributes:
        result: The analysis result.
        processing_time: Time taken to generate the result, in seconds.
    """

    result: AnalysisResult
    processing_time: float
