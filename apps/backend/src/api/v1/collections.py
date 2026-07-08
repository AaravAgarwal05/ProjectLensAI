"""REST API endpoints for collection CRUD and report membership management.

All business logic is delegated to ``CollectionService``.  The router only
handles HTTP concerns (parsing, status codes, error formatting).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.services import CollectionService

from .schemas import (
    CollectionListResponse,
    CollectionResponse,
    CreateCollectionRequest,
    UpdateCollectionRequest,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Collection CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    body: CreateCollectionRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> CollectionResponse:
    """Create a new collection."""
    service = CollectionService(session=db)
    collection = await service.create(name=body.name, description=body.description)
    return CollectionResponse.model_validate(collection)


@router.get("", response_model=CollectionListResponse)
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CollectionListResponse:
    """List all collections (paginated)."""
    service = CollectionService(session=db)
    collections, total = await service.list(skip=skip, limit=limit)
    return CollectionListResponse(
        items=[CollectionResponse.model_validate(c) for c in collections],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Retrieve a single collection by ID."""
    service = CollectionService(session=db)
    collection = await service.get(collection_id)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection {collection_id} not found",
        )
    resp = CollectionResponse.model_validate(collection)
    resp.report_count = len(collection.reports)
    return resp


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    body: UpdateCollectionRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> CollectionResponse:
    """Partially update collection metadata.

    Only the fields present in the JSON body are applied; omitted fields
    are left unchanged.
    """
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    service = CollectionService(session=db)
    collection = await service.update(collection_id, **updates)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection {collection_id} not found",
        )
    return CollectionResponse.model_validate(collection)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    """Delete a collection (does not delete its member reports)."""
    service = CollectionService(session=db)
    deleted = await service.delete(collection_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection {collection_id} not found",
        )


# ---------------------------------------------------------------------------
# Report membership
# ---------------------------------------------------------------------------


@router.post(
    "/{collection_id}/reports/{report_id}",
    status_code=status.HTTP_200_OK,
)
async def add_report_to_collection(
    collection_id: UUID,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    """Link a report to a collection (idempotent: no-op if already linked)."""
    service = CollectionService(session=db)
    collection = await service.get(collection_id)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection {collection_id} not found",
        )
    await service.add_report(collection_id, report_id)
    return {"message": "Report added to collection"}


@router.delete(
    "/{collection_id}/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_report_from_collection(
    collection_id: UUID,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> None:
    """Unlink a report from a collection (idempotent)."""
    service = CollectionService(session=db)
    await service.remove_report(collection_id, report_id)
