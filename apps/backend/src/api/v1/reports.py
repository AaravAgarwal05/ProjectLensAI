"""REST API endpoints for report CRUD and version management.

All business logic is delegated to ``ReportService``.  The router only
handles HTTP concerns (parsing, status codes, error formatting).
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db, get_settings
from src.config.settings import AppSettings
from src.database.session import async_session_factory
from src.document_processing.cleaners.artifacts import PageArtifactCleaner
from src.document_processing.cleaners.base import CleaningPipeline
from src.document_processing.cleaners.unicode import UnicodeCleaner
from src.document_processing.cleaners.whitespace import WhitespaceCleaner
from src.document_processing.metadata import MetadataExtractor
from src.document_processing.parsers.docx import DOCXParser
from src.document_processing.parsers.pdf import PDFParser
from src.document_processing.parsers.registry import ParserRegistry
from src.document_processing.parsers.text import TextParser
from src.document_processing.pipeline import ProcessingPipeline
from src.services import ProcessingService, ReportService
from src.storage import LocalStorageProvider, SupabaseStorageProvider
from src.storage.base import StorageProvider

from .schemas import (
    ReportListResponse,
    ReportResponse,
    UpdateReportRequest,
    VersionResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_storage_provider(settings: AppSettings) -> StorageProvider:
    """Instantiate the storage backend configured in ``settings``."""
    if settings.STORAGE_PROVIDER == "supabase":
        return SupabaseStorageProvider(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_KEY,
            bucket_name=settings.SUPABASE_STORAGE_BUCKET,
        )
    return LocalStorageProvider(base_path=settings.STORAGE_LOCAL_PATH)


def _build_processing_pipeline() -> ProcessingPipeline:
    """Build a default ``ProcessingPipeline`` with all available parsers and cleaners.

    Each parser is registered with the ``ParserRegistry``; optional
    dependencies (PyMuPDF, python-docx) are handled gracefully by the
    parsers themselves at runtime.
    """
    registry = ParserRegistry()
    registry.register(PDFParser)
    registry.register(DOCXParser)
    registry.register(TextParser)

    cleaners = CleaningPipeline(
        [
            WhitespaceCleaner(),
            UnicodeCleaner(),
            PageArtifactCleaner(),
        ],
    )

    return ProcessingPipeline(
        parser_registry=registry,
        cleaner_pipeline=cleaners,
        metadata_extractor=MetadataExtractor(),
    )


def _build_processing_service(settings: AppSettings) -> ProcessingService:
    """Assemble a ``ProcessingService`` from its component dependencies.

    Because ``ProcessingService`` is created per-request for the background
    task, this factory makes it easy to swap implementations in tests.
    """
    pipeline = _build_processing_pipeline()
    storage = _build_storage_provider(settings)

    # ``async_session_factory`` is an ``async_sessionmaker`` installed
    # during bootstrap.  It is a ``Callable[[], AsyncSession]``.
    return ProcessingService(
        pipeline=pipeline,
        storage=storage,
        db_factory=async_session_factory,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Report CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str | None = Form(None),
    department: str | None = Form(None),
    author: str | None = Form(None),
    tags: str | None = Form(None),
    visibility: str = Form("private"),
    year: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
    settings: AppSettings = Depends(get_settings),
    user: dict = Depends(get_current_user),
) -> ReportResponse:
    """Upload a new report together with its initial file (v1).

    Metadata fields are sent as multipart form parts alongside the file.
    After the report is created, background processing is triggered
    automatically so the endpoint returns immediately (HTTP 201).
    """
    tag_list: list[str] | None = (
        [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    )

    service = ReportService(
        session=db,
        storage=_build_storage_provider(settings),
        settings=settings,
    )
    report = await service.create_report(
        file=file,
        title=title,
        description=description,
        department=department,
        author=author,
        tags=tag_list,
        visibility=visibility,
        year=year,
    )

    # Trigger background processing so the user gets an immediate response.
    processing_service = _build_processing_service(settings)
    background_tasks.add_task(processing_service.process_report, report.id)

    return ReportResponse.model_validate(report)


@router.get("", response_model=ReportListResponse)
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    author: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: AppSettings = Depends(get_settings),
) -> ReportListResponse:
    """List reports with optional status / author / text search filters."""
    service = ReportService(
        session=db,
        storage=_build_storage_provider(settings),
        settings=settings,
    )
    reports, total = await service.list_reports(
        skip=skip,
        limit=limit,
        status=status,
        author=author,
        search=search,
    )
    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    settings: AppSettings = Depends(get_settings),
) -> ReportResponse:
    """Retrieve a single report by ID, including all version history."""
    service = ReportService(
        session=db,
        storage=_build_storage_provider(settings),
        settings=settings,
    )
    report = await service.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: UUID,
    body: UpdateReportRequest,
    db: AsyncSession = Depends(get_db),
    settings: AppSettings = Depends(get_settings),
    user: dict = Depends(get_current_user),
) -> ReportResponse:
    """Partially update report metadata.

    Only the fields present in the JSON body are applied; omitted fields
    are left unchanged.
    """
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    service = ReportService(
        session=db,
        storage=_build_storage_provider(settings),
        settings=settings,
    )
    report = await service.update_report(report_id, **updates)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    return ReportResponse.model_validate(report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    settings: AppSettings = Depends(get_settings),
    user: dict = Depends(get_current_user),
) -> None:
    """Delete a report and all its version files from storage."""
    service = ReportService(
        session=db,
        storage=_build_storage_provider(settings),
        settings=settings,
    )
    deleted = await service.delete_report(report_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------


@router.post(
    "/{report_id}/versions",
    response_model=VersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_version(
    report_id: UUID,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    settings: AppSettings = Depends(get_settings),
    user: dict = Depends(get_current_user),
) -> VersionResponse:
    """Upload a new file version for an existing report.

    After the version is created, background processing is triggered
    automatically to re-process the report content.
    """
    service = ReportService(
        session=db,
        storage=_build_storage_provider(settings),
        settings=settings,
    )
    version = await service.upload_new_version(report_id=report_id, file=file)

    # Trigger background processing for the new version content.
    processing_service = _build_processing_service(settings)
    background_tasks.add_task(processing_service.process_report, report_id)

    return VersionResponse.model_validate(version)


@router.get("/{report_id}/versions", response_model=list[VersionResponse])
async def list_versions(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    settings: AppSettings = Depends(get_settings),
) -> list[VersionResponse]:
    """List all versions for a report, ordered by version number."""
    service = ReportService(
        session=db,
        storage=_build_storage_provider(settings),
        settings=settings,
    )
    report = await service.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    return [VersionResponse.model_validate(v) for v in report.versions]
