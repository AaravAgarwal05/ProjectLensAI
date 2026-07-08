"""Async database engine and session factory."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

_engine = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str) -> None:
    """Create the global async engine and session factory.

    Called once during application bootstrap.

    Args:
        database_url: Full asyncpg connection string.
    """
    global _engine, async_session_factory  # noqa: PLW0603

    _engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

    async_session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Verify connectivity
    async with _engine.connect() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )

    logger.info("Database engine created for %s", database_url.split("@")[-1])


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yield an async database session.

    The session is automatically committed on success or rolled back on error.
    """
    if async_session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Dispose of the engine — should be called on shutdown."""
    global _engine, async_session_factory  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        async_session_factory = None
        logger.info("Database engine disposed")
