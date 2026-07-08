"""Repository for Collection model operations."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Collection, CollectionReport, Report
from src.repository.base import BaseRepository


class CollectionRepository(BaseRepository[Collection]):
    """Repository for Collection CRUD with collection-specific queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Collection, session=session)

    async def get_by_name(self, name: str) -> Collection | None:
        """Retrieve a collection by its unique name."""
        stmt = select(Collection).where(Collection.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_report(self, collection_id: UUID, report_id: UUID) -> None:
        """Link a report to a collection (no-op if already linked)."""
        stmt = select(CollectionReport).where(
            CollectionReport.collection_id == collection_id,
            CollectionReport.report_id == report_id,
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return

        association = CollectionReport(
            collection_id=collection_id,
            report_id=report_id,
        )
        self.session.add(association)
        await self.session.flush()

    async def remove_report(self, collection_id: UUID, report_id: UUID) -> None:
        """Unlink a report from a collection (no-op if not linked)."""
        stmt = select(CollectionReport).where(
            CollectionReport.collection_id == collection_id,
            CollectionReport.report_id == report_id,
        )
        result = await self.session.execute(stmt)
        association = result.scalar_one_or_none()
        if association is None:
            return

        await self.session.delete(association)
        await self.session.flush()

    async def get_reports_for_collection(
        self,
        collection_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Report]:
        """Return reports belonging to a collection."""
        stmt = (
            select(Report)
            .join(CollectionReport, Report.id == CollectionReport.report_id)
            .where(CollectionReport.collection_id == collection_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
