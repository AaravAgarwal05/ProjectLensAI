"""REST API endpoints for report CRUD and version management.

All business logic is delegated to ``ReportService``.  The router only
handles HTTP concerns (parsing, status codes, error formatting).
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.config.settings import AppSettings, get_settings
from src.database import session as db_session
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

logger = logging.getLogger(__name__)
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
        db_factory=db_session.async_session_factory,  # type: ignore[arg-type]
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
    logger.info("═► UPLOAD: Receiving file '%s' (title='%s', size=%d bytes)...",
                file.filename, title, file.size or 0)
    logger.info("  └── File type: %s | Department: %s | Author: %s",
                file.content_type, department or "not specified", author or "not specified")

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

    logger.info("  ✔ File saved to storage. Report created with ID: %s", report.id)
    logger.info("  └── Saving was done, now triggering background analysis...")

    # Commit the transaction NOW so the background task can see the new
    # report when it opens its own session.  (get_db's dependency cleanup
    # commits after background tasks — too late.)
    await db.commit()

    # Trigger background processing so the user gets an immediate response.
    processing_service = _build_processing_service(settings)
    background_tasks.add_task(
        processing_service.process_report,
        report.id,
        str(user.id),
        getattr(user, "preferences", None),
    )

    logger.info("  ✔ Background analysis started! The report will be processed in the background.")
    logger.info("  └── You can continue using the app while it's being analyzed.")

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
    background_tasks.add_task(
        processing_service.process_report,
        report_id,
        str(user.id),
        getattr(user, "preferences", None),
    )

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


# ---------------------------------------------------------------------------
# Search / retrieval (eval-facing)
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    """Search a report's indexed chunks."""

    query: str
    top_k: int = 25


class SearchResultChunk(BaseModel):
    """A single chunk returned from search."""

    chunk_id: str
    content: str
    score: float
    section_name: str = ""
    page_number: int | None = None


class SearchResponse(BaseModel):
    """Ranked search results."""

    chunks: list[SearchResultChunk]
    total: int = 0


def _get_chroma_client(request: Request) -> Any | None:
    """Get the shared ChromaDB client from app state."""
    client = getattr(request.app.state, "chroma_client", None)
    return client


@router.post("/{report_id}/search", response_model=SearchResponse)
async def search_report_chunks(
    report_id: str,
    body: SearchRequest,
    request: Request,
    settings: AppSettings = Depends(get_settings),
) -> SearchResponse:
    """Search a report's indexed chunks by embedding similarity.

    Returns the raw ranked list of chunks (no reranking) for evaluation.
    """
    client = _get_chroma_client(request)
    if client is None:
        raise HTTPException(status_code=503, detail="ChromaDB not available")

    try:
        collection = client.get_collection(name=f"report_{report_id}")
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"ChromaDB collection for report {report_id} not found",
        ) from None

    from src.ai_core.embedding.providers.ollama import OllamaEmbeddingProvider

    embedder = OllamaEmbeddingProvider(
        model_name="nomic-embed-text",
        base_url=settings.ollama_base_url,
    )
    query_vec = await embedder.embed(body.query)

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=body.top_k,
        include=["metadatas", "distances", "documents"],
    )

    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    chunks: list[SearchResultChunk] = []
    for i in range(len(ids)):
        score = 1.0 / (1.0 + distances[i]) if distances and i < len(distances) else 0.0
        meta = metadatas[i] if metadatas and i < len(metadatas) else {}
        chunks.append(
            SearchResultChunk(
                chunk_id=ids[i],
                content=documents[i] if documents and i < len(documents) else "",
                score=score,
                section_name=meta.get("section_name", "") or "",
                page_number=meta.get("page_number"),
            )
        )

    return SearchResponse(chunks=chunks, total=len(chunks))
