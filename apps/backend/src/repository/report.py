"""Repository for Report model operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models import Report
from src.repository.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for Report CRUD with report-specific queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Report, session=session)

    async def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Report]:
        """Return reports filtered by status, ordered by creation date."""
        stmt = (
            select(Report)
            .where(Report.status == status)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_author(
        self,
        author: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Report]:
        """Return reports filtered by author."""
        stmt = (
            select(Report)
            .where(Report.author == author)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Report]:
        """Search reports by ILIKE on title and description."""
        pattern = f"%{query}%"
        stmt = (
            select(Report)
            .where(
                Report.title.ilike(pattern)
                | Report.description.ilike(pattern)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_versions(self, report_id: UUID) -> Report | None:
        """Retrieve a report with its versions eagerly loaded."""
        stmt = (
            select(Report)
            .options(joinedload(Report.versions))
            .where(Report.id == report_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def update_status(self, report_id: UUID, status: str) -> Report | None:
        """Update only the ``status`` field of a report.

        More targeted than a full ``update()`` when only the processing
        status changes.  Returns the updated ``Report`` or ``None`` if no
        report with that ID exists.
        """
        report = await self.get(report_id)
        if report is None:
            return None
        report.status = status
        await self.session.flush()
        return report

    async def count_by_status(self, status: str) -> int:
        """Count reports with the given status."""
        stmt = select(func.count(Report.id)).where(Report.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()
