"""Document management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.config.settings import get_settings
from src.config.settings import AppSettings

router = APIRouter()


class DocumentResponse(BaseModel):
    """Lightweight document schema returned by API responses."""

    id: UUID
    filename: str
    content_type: str
    status: str
    created_at: str


class PaginatedDocuments(BaseModel):
    """Paginated list of documents."""

    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=PaginatedDocuments)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    settings: AppSettings = Depends(get_settings),
) -> PaginatedDocuments:
    """List all documents for the current user (paginated).

    This is a placeholder — full implementation will follow.
    """
    return PaginatedDocuments(items=[], total=0, page=page, page_size=page_size)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    settings: AppSettings = Depends(get_settings),
) -> DocumentResponse:
    """Upload a new document.

    This is a placeholder — full implementation will follow.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document upload not yet implemented",
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    settings: AppSettings = Depends(get_settings),
) -> DocumentResponse:
    """Retrieve a document by its unique identifier.

    This is a placeholder — full implementation will follow.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Document {document_id} retrieval not yet implemented",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    settings: AppSettings = Depends(get_settings),
) -> None:
    """Delete a document by its unique identifier.

    This is a placeholder — full implementation will follow.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Document {document_id} deletion not yet implemented",
    )
