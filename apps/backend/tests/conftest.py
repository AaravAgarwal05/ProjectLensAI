"""Pytest fixtures and helpers for ProjectLens backend tests.

Supplies mock storage, settings, services, and an API client with
FastAPI dependency overrides for isolated testing of the report
management stack (reports, collections, versions).
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.config.settings import AppSettings, get_settings as _cached_get_settings
from src.database.models import Collection, Report, ReportVersion
from src.main import create_app
from src.services import CollectionService, ReportService
from src.storage.base import StorageProvider


# ======================================================================
# Test data factories
# ======================================================================


def make_report(**overrides: object) -> Report:
    """Build a ``Report`` instance with sensible defaults for testing.

    Keyword arguments override any default field, making it easy to
    customise a single attribute without repeating the rest.
    """
    now = datetime.now(timezone.utc)
    defaults: dict[str, object] = {
        "id": uuid4(),
        "title": "Test Report",
        "description": "A test report description",
        "department": "Engineering",
        "author": "Test Author",
        "tags": ["test", "engineering"],
        "visibility": "private",
        "year": 2024,
        "status": "uploaded",
        "storage_provider": "supabase",
        "storage_path": "reports/test_id/test.pdf",
        "original_filename": "test.pdf",
        "mime_type": "application/pdf",
        "checksum": "abc123def456",
        "file_size": 12345,
        "created_at": now,
        "updated_at": now,
        "versions": [],
    }
    defaults.update(overrides)
    return Report(**defaults)  # type: ignore[arg-type]


def make_version(**overrides: object) -> ReportVersion:
    """Build a ``ReportVersion`` instance with sensible defaults."""
    now = datetime.now(timezone.utc)
    defaults: dict[str, object] = {
        "id": uuid4(),
        "report_id": uuid4(),
        "version_number": 1,
        "storage_path": "reports/test_id/test.pdf",
        "original_filename": "test.pdf",
        "mime_type": "application/pdf",
        "checksum": "abc123def456",
        "file_size": 12345,
        "created_at": now,
    }
    defaults.update(overrides)
    return ReportVersion(**defaults)  # type: ignore[arg-type]


def make_collection(**overrides: object) -> Collection:
    """Build a ``Collection`` instance with sensible defaults."""
    now = datetime.now(timezone.utc)
    defaults: dict[str, object] = {
        "id": uuid4(),
        "name": "Test Collection",
        "description": "A test collection description",
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Collection(**defaults)  # type: ignore[arg-type]


def _report_from_response(data: dict) -> Report:
    """Create a Report instance from API response data for testing."""
    return Report(
        id=UUID(data["id"]),
        title=data["title"],
        description=data.get("description"),
        department=data.get("department"),
        author=data.get("author"),
        tags=data.get("tags"),
        visibility=data["visibility"],
        year=data.get("year"),
        status=data["status"],
        original_filename=data.get("original_filename"),
        mime_type=data.get("mime_type"),
        checksum=data.get("checksum"),
        file_size=data.get("file_size"),
    )


# ======================================================================
# Core fixtures
# ======================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Session-scoped event loop for async fixtures."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mock_session() -> AsyncMock:
    """Return a mock ``AsyncSession`` with safe defaults for all CRUD paths.

    The mock allows any method call on ``execute()`` return values so
    that intermediate chaining (``scalars`` / ``all`` / ``scalar_one``)
    does not fail.
    """
    session: AsyncMock = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    # Make execute chains safe by default.
    # NOTE: The result proxy is a MagicMock (sync), NOT an AsyncMock, because
    # its methods (scalar_one, scalars().all, scalar_one_or_none) are all
    # synchronous calls on the SQLAlchemy result object.
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    execute_result.scalar_one_or_none.return_value = None
    execute_result.scalar_one.return_value = 0
    session.execute.return_value = execute_result
    session.get.return_value = None
    return session


@pytest_asyncio.fixture
async def mock_storage() -> AsyncMock:
    """Mock ``StorageProvider`` with sensible defaults.

    ``store`` returns a plausible report path; ``retrieve`` returns
    dummy binary content.
    """
    storage: AsyncMock = AsyncMock(spec=StorageProvider)
    storage.store.return_value = "reports/test_id/test.pdf"
    storage.retrieve.return_value = b"test file content"
    storage.exists.return_value = True
    return storage


@pytest.fixture
def mock_settings() -> AppSettings:
    """AppSettings tuned for testing (small upload limit, limited extensions)."""
    return AppSettings(
        MAX_UPLOAD_SIZE=1024 * 100,  # 100 KiB
        ALLOWED_EXTENSIONS=[".pdf", ".docx", ".txt"],
        STORAGE_PROVIDER="local",
        STORAGE_LOCAL_PATH="/tmp/test_storage_projectlens",
    )


@pytest_asyncio.fixture
async def report_service(
    mock_session: AsyncSession,
    mock_storage: StorageProvider,
    mock_settings: AppSettings,
) -> ReportService:
    """``ReportService`` wired with mocked session, storage and settings."""
    return ReportService(session=mock_session, storage=mock_storage, settings=mock_settings)


@pytest_asyncio.fixture
async def collection_service(
    mock_session: AsyncSession,
) -> CollectionService:
    """``CollectionService`` wired with a mocked session."""
    return CollectionService(session=mock_session)


# ======================================================================
# API-level fixtures (with FastAPI dependency overrides)
# ======================================================================


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client against the application (no server needed, no overrides).

    The health-check endpoint does not require authentication, so this
    fixture omits dependency overrides.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def api_client(
    mock_settings: AppSettings,
) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client with all external dependencies overridden.

    Overrides applied:
    * ``get_db`` — returns a mock ``AsyncSession`` (no real DB)
    * ``get_current_user`` — returns a placeholder user dict
    * ``get_settings`` — returns the test ``mock_settings``
    """
    app = create_app()

    mock_session: AsyncMock = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    execute_result.scalar_one_or_none.return_value = None
    execute_result.scalar_one.return_value = 0
    mock_session.execute.return_value = execute_result
    mock_session.get.return_value = None

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield mock_session  # type: ignore[misc]

    async def _override_user() -> dict:
        return {"sub": "test-user-id", "role": "user"}

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[_cached_get_settings] = lambda: mock_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
