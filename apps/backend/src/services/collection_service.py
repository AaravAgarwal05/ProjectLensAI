"""Service layer for collection management."""

import logging
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Collection
from src.repository.collection import CollectionRepository

logger = logging.getLogger(__name__)


class CollectionService:
    """Business logic for managing collections of reports."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = CollectionRepository(session)
        self._session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(
        self,
        name: str,
        description: str | None = None,
    ) -> Collection:
        """Create a new collection."""
        collection = await self._repo.create(name=name, description=description)
        logger.info("Created collection '%s' (id=%s)", name, collection.id)
        return collection

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Collection], int]:
        """Return a paginated list of collections and the total count."""
        collections = await self._repo.list(skip=skip, limit=limit)

        total_stmt = select(func.count(Collection.id))
        total = (await self._session.execute(total_stmt)).scalar_one()

        return collections, total

    async def get(self, collection_id: UUID) -> Collection | None:
        """Retrieve a single collection by ID."""
        return await self._repo.get(collection_id)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(
        self,
        collection_id: UUID,
        **updates: Any,
    ) -> Collection | None:
        """Update collection metadata.  Returns ``None`` if not found."""
        return await self._repo.update(collection_id, **updates)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, collection_id: UUID) -> bool:
        """Delete a collection.  Returns ``True`` if it existed."""
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
    ) -> None:
        """Link a report to a collection."""
        await self._repo.add_report(collection_id, report_id)
        logger.debug("Added report %s to collection %s", report_id, collection_id)

    async def remove_report(
        self,
        collection_id: UUID,
        report_id: UUID,
    ) -> None:
        """Unlink a report from a collection."""
        await self._repo.remove_report(collection_id, report_id)
        logger.debug("Removed report %s from collection %s", report_id, collection_id)
