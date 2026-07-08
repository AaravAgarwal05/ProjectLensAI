"""Postgres-backed memory provider."""

import json
import logging
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, func, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base import Base
from src.memory.base import MemoryProvider

logger = logging.getLogger(__name__)


class MemoryEntry(Base):
    """SQLAlchemy model for memory entries stored in Postgres."""

    __tablename__ = "memory_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PostgresMemoryProvider(MemoryProvider):
    """Key-value memory backed by a Postgres ``memory_entries`` table.

    Uses JSONB for flexible value storage and ``ILIKE`` for basic
    text-based search.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store(self, key: str, value: Any) -> None:
        stmt = select(MemoryEntry).where(MemoryEntry.key == key)
        result = await self._session.execute(stmt)
        entry = result.scalar_one_or_none()

        if entry is None:
            entry = MemoryEntry(key=key, value=value)
            self._session.add(entry)
        else:
            entry.value = value

        await self._session.flush()
        logger.debug("Stored memory entry: %s", key)

    async def retrieve(self, key: str) -> Any | None:
        stmt = select(MemoryEntry).where(MemoryEntry.key == key)
        result = await self._session.execute(stmt)
        entry = result.scalar_one_or_none()
        return entry.value if entry else None

    async def delete(self, key: str) -> None:
        stmt = select(MemoryEntry).where(MemoryEntry.key == key)
        result = await self._session.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry:
            await self._session.delete(entry)
            await self._session.flush()
            logger.debug("Deleted memory entry: %s", key)

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        pattern = f"%{query}%"
        stmt = (
            select(MemoryEntry)
            .where(MemoryEntry.value.cast(String).ilike(pattern))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        entries = result.scalars().all()
        return [
            {"key": e.key, "value": e.value, "created_at": str(e.created_at)}
            for e in entries
        ]
