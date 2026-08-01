"""Service layer for collection management."""

import logging
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.exceptions import ProjectLensError
from src.database.models import Collection, Report
from src.repository.collection import CollectionRepository

logger = logging.getLogger(__name__)


class CollectionService:
    """Business logic for managing collections of reports.

    Every operation is scoped to ``owner_id`` so a user can never see or
    mutate another user's collections (cross-tenant IDOR guard).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = CollectionRepository(session)
        self._session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(
        self,
        name: str,
        owner_id: str,
        description: str | None = None,
    ) -> Collection:
        """Create a new collection owned by ``owner_id``."""
        collection = await self._repo.create(
            name=name, owner_id=owner_id, description=description
        )
        logger.info("Created collection '%s' (id=%s)", name, collection.id)
        return collection

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def list(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Collection], int]:
        """Return the caller's collections (paginated) and the total count."""
        collections = await self._repo.list(
            owner_id=owner_id, skip=skip, limit=limit
        )

        total_stmt = select(func.count(Collection.id)).where(
            Collection.owner_id == owner_id
        )
        total = (await self._session.execute(total_stmt)).scalar_one()

        return collections, total

    async def get(self, collection_id: UUID, owner_id: str) -> Collection | None:
        """Retrieve a collection — only if the caller owns it."""
        collection = await self._repo.get(collection_id)
        return self._ensure_owned(collection, collection_id, owner_id)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(
        self,
        collection_id: UUID,
        owner_id: str,
        **updates: Any,
    ) -> Collection | None:
        """Update collection metadata the caller owns."""
        existing = self._ensure_owned(
            await self._repo.get(collection_id), collection_id, owner_id
        )
        return await self._repo.update(existing.id, **updates)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, collection_id: UUID, owner_id: str) -> bool:
        """Delete a collection the caller owns.  Returns ``True`` if deleted."""
        self._ensure_owned(
            await self._repo.get(collection_id), collection_id, owner_id
        )
        deleted = await self._repo.delete(collection_id)
        if deleted:
            logger.info("Deleted collection %s", collection_id)
        return deleted

    # ------------------------------------------------------------------
    # Report membership
    # ------------------------------------------------------------------

    async def add_report(
        self,
        collection_id: UUID,
        report_id: UUID,
        owner_id: str,
    ) -> None:
        """Link a report to a collection — both must belong to the caller."""
        self._ensure_owned(
            await self._repo.get(collection_id), collection_id, owner_id
        )
        self._ensure_owned(
            await self._session.get(Report, report_id), report_id, owner_id
        )
        await self._repo.add_report(collection_id, report_id)
        logger.debug("Added report %s to collection %s", report_id, collection_id)

    async def remove_report(
        self,
        collection_id: UUID,
        report_id: UUID,
        owner_id: str,
    ) -> None:
        """Unlink a report from a collection the caller owns."""
        self._ensure_owned(
            await self._repo.get(collection_id), collection_id, owner_id
        )
        await self._repo.remove_report(collection_id, report_id)
        logger.debug("Removed report %s from collection %s", report_id, collection_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_owned(
        collection: Collection | None, collection_id: UUID, owner_id: str
    ) -> Collection:
        """Return the collection or 404 — never reveals whether an id exists."""
        if collection is None or str(collection.owner_id) != str(owner_id):
            raise ProjectLensError(
                message=f"Collection {collection_id} not found",
                code="collection_not_found",
                status_code=404,
            )
        return collection
