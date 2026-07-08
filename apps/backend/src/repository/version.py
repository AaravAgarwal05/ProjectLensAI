"""Repository for ReportVersion model operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ReportVersion
from src.repository.base import BaseRepository


class VersionRepository(BaseRepository[ReportVersion]):
    """Repository for ReportVersion CRUD with version-specific queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=ReportVersion, session=session)

    async def get_versions_for_report(
        self,
        report_id: UUID,
    ) -> list[ReportVersion]:
        """Return all versions for a report, ordered by version number."""
        stmt = (
            select(ReportVersion)
            .where(ReportVersion.report_id == report_id)
            .order_by(ReportVersion.version_number.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_version(
        self,
        report_id: UUID,
    ) -> ReportVersion | None:
        """Return the most recent version for a report."""
        stmt = (
            select(ReportVersion)
            .where(ReportVersion.report_id == report_id)
            .order_by(ReportVersion.version_number.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_next_version_number(self, report_id: UUID) -> int:
        """Return the next version number for a report (max + 1, or 1 if no versions exist)."""
        stmt = (
            select(func.max(ReportVersion.version_number))
            .where(ReportVersion.report_id == report_id)
        )
        result = await self.session.execute(stmt)
        max_version = result.scalar_one()
        return (max_version + 1) if max_version is not None else 1
