"""Analysis / insight endpoints."""


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.config.settings import AppSettings, get_settings

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request payload to trigger a new analysis."""

    document_ids: list[str]
    analysis_type: str = "summary"


class AnalysisResponse(BaseModel):
    """Response returned after analysis completes."""

    id: str
    status: str
    result: dict | None = None


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def trigger_analysis(
    body: AnalysisRequest,
    settings: AppSettings = Depends(get_settings),
) -> AnalysisResponse:
    """Trigger a new analysis job for the specified documents.

    This is a placeholder — full implementation will follow.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Analysis not yet implemented",
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_results(
    analysis_id: str,
    settings: AppSettings = Depends(get_settings),
) -> AnalysisResponse:
    """Retrieve results for a previously submitted analysis.

    This is a placeholder — full implementation will follow.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Analysis {analysis_id} retrieval not yet implemented",
    )
