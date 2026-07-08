"""Service layer for report CRUD and version management."""

import hashlib
import logging
import uuid
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.exceptions import ProjectLensError
from src.config.settings import AppSettings
from src.database.models import Report, ReportVersion
from src.repository.report import ReportRepository
from src.repository.version import VersionRepository
from src.storage.base import StorageProvider

logger = logging.getLogger(__name__)


class ReportService:
    """Business logic for managing reports and their versions.

    All dependencies are injected via ``__init__`` so callers compose
    the object themselves (no global state, no hidden imports).
    """

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageProvider,
        settings: AppSettings,
    ) -> None:
        self._report_repo = ReportRepository(session)
        self._version_repo = VersionRepository(session)
        self._storage = storage
        self._settings = settings
        self._session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_report(
        self,
        file: UploadFile,
        title: str,
        description: str | None = None,
        department: str | None = None,
        author: str | None = None,
        tags: list[str] | None = None,
        visibility: str = "private",
        year: int | None = None,
    ) -> Report:
        """Upload a new report file and create its initial version (v1).

        Steps:
        1. Validate file extension and size.
        2. Read content and compute SHA-256 checksum.
        3. Store raw bytes in the configured storage backend.
        4. Persist a ``Report`` row with status ``uploaded``.
        5. Persist a ``ReportVersion`` row for v1.

        Returns the newly created ``Report``.
        """
        self._validate_file(file=file)

        content = await file.read()
        checksum = self._compute_checksum(content)

        storage_path = await self._store_file(file=file, content=content)

        report = await self._report_repo.create(
            title=title,
            description=description,
            department=department,
            author=author,
            tags=tags,
            visibility=visibility,
            year=year,
            status="uploaded",
            storage_provider="supabase",
            storage_path=storage_path,
            original_filename=file.filename,
            mime_type=file.content_type,
            checksum=checksum,
            file_size=len(content),
        )

        await self._version_repo.create(
            report_id=report.id,
            version_number=1,
            storage_path=storage_path,
            original_filename=file.filename or "unknown",
            mime_type=file.content_type or "application/octet-stream",
            checksum=checksum,
            file_size=len(content),
        )

        logger.info(
            "Created report '%s' (id=%s) v1 — %s",
            title, report.id, file.filename,
        )
        return report

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_report(self, report_id: UUID) -> Report | None:
        """Retrieve a single report by ID."""
        return await self._report_repo.get(report_id)

    async def list_reports(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        author: str | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[Report], int]:
        """Return a paginated, optionally filtered list of reports and the total count.

        Filters are combined with AND semantics.  ``search`` performs a
        case-insensitive match against both ``title`` and ``description``.
        """
        conditions: list[Any] = []
        if status is not None:
            conditions.append(Report.status == status)
        if author is not None:
            conditions.append(Report.author == author)
        if search is not None:
            pattern = f"%{search}%"
            conditions.append(
                Report.title.ilike(pattern)
                | Report.description.ilike(pattern)
            )

        # Total count
        count_stmt = select(func.count(Report.id))
        for c in conditions:
            count_stmt = count_stmt.where(c)
        total = (await self._session.execute(count_stmt)).scalar_one()

        # Paginated results
        fetch_stmt = select(Report)
        for c in conditions:
            fetch_stmt = fetch_stmt.where(c)
        fetch_stmt = fetch_stmt.offset(skip).limit(limit)
        rows = (await self._session.execute(fetch_stmt)).scalars().all()

        return list(rows), total

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_report(
        self,
        report_id: UUID,
        **updates: Any,
    ) -> Report | None:
        """Update metadata on an existing report.  Returns ``None`` if not found."""
        return await self._report_repo.update(report_id, **updates)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_report(self, report_id: UUID) -> bool:
        """Delete a report and its storage files for *all* versions.

        Returns ``True`` if the report existed and was deleted, ``False`` if
        no report with that ID was found.
        """
        report = await self._report_repo.get_with_versions(report_id)
        if report is None:
            return False

        # Remove stored files for every version so orphaned blobs don't
        # accumulate in the storage backend.
        for version in report.versions:
            try:
                await self._storage.delete(version.storage_path)
            except Exception:
                logger.warning(
                    "Failed to delete storage path '%s' for report %s",
                    version.storage_path,
                    report_id,
                )

        # Delete the primary report row — cascade handles the version rows.
        deleted = await self._report_repo.delete(report_id)
        if deleted:
            logger.info("Deleted report %s and %d version(s)", report_id, len(report.versions))
        return deleted

    # ------------------------------------------------------------------
    # Versions
    # ------------------------------------------------------------------

    async def upload_new_version(
        self,
        report_id: UUID,
        file: UploadFile,
    ) -> ReportVersion:
        """Upload a new file version for an existing report.

        Validates the file, stores it, and creates a ``ReportVersion`` row
        with an auto-incremented version number.
        """
        # Verify the report exists first.
        existing = await self._report_repo.get(report_id)
        if existing is None:
            raise ProjectLensError(
                message=f"Report {report_id} not found",
                code="report_not_found",
                status_code=404,
            )

        self._validate_file(file=file)

        content = await file.read()
        checksum = self._compute_checksum(content)

        storage_path = await self._store_file(file=file, content=content)

        next_version = await self._version_repo.get_next_version_number(report_id)

        version = await self._version_repo.create(
            report_id=report_id,
            version_number=next_version,
            storage_path=storage_path,
            original_filename=file.filename or "unknown",
            mime_type=file.content_type or "application/octet-stream",
            checksum=checksum,
            file_size=len(content),
        )

        logger.info(
            "Uploaded version %d for report %s (%s)",
            next_version, report_id, file.filename,
        )
        return version

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _store_file(self, file: UploadFile, content: bytes) -> str:
        """Generate a unique storage path and persist the file."""
        file_id = uuid.uuid4().hex
        storage_path = f"reports/{file_id}/{file.filename}"
        await self._storage.store(storage_path, content)
        return storage_path

    def _validate_file(self, file: UploadFile) -> None:
        """Validate file extension and size.  Raises ``ProjectLensError``."""
        # Extension check
        if file.filename:
            ext = _extension(file.filename)
            if ext not in self._settings.ALLOWED_EXTENSIONS:
                raise ProjectLensError(
                    message=(
                        f"File extension '{ext}' is not allowed. "
                        f"Allowed: {', '.join(self._settings.ALLOWED_EXTENSIONS)}"
                    ),
                    code="invalid_file_extension",
                    status_code=400,
                )

        # Size check via Content-Length header (when available).
        if file.size is not None and file.size > self._settings.MAX_UPLOAD_SIZE:
            raise ProjectLensError(
                message=(
                    f"File exceeds the maximum upload size of "
                    f"{self._settings.MAX_UPLOAD_SIZE / (1024 * 1024):.0f} MiB."
                ),
                code="file_too_large",
                status_code=413,
            )

    @staticmethod
    def _compute_checksum(content: bytes) -> str:
        """Return the hex-encoded SHA-256 digest of ``content``."""
        return hashlib.sha256(content).hexdigest()


def _extension(filename: str) -> str:
    """Return the lower-case file extension including the leading dot."""
    idx = filename.rfind(".")
    return filename[idx:].lower() if idx != -1 else ""
