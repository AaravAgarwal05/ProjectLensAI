"""Session Manager — CRUD operations for chat sessions."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.chat.database import ChatSessionModel

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages chat session lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_session(
        self,
        title: str = "New Chat",
        report_ids: list[str] | None = None,
        mode: str = "single",
    ) -> ChatSessionModel:
        """Create a new chat session."""
        session = ChatSessionModel(
            title=title,
            mode=mode,
            report_ids=report_ids or [],
        )
        self._db.add(session)
        await self._db.flush()
        logger.debug("Created session %s", session.id)
        return session

    async def get_session(self, session_id: str) -> ChatSessionModel | None:
        """Get a session by ID."""
        result = await self._db.execute(
            select(ChatSessionModel).where(ChatSessionModel.id == session_id)
        )
        return result.scalar_one_or_none()

    async def update_session(self, session_id: str, **kwargs: Any) -> ChatSessionModel | None:
        """Update session fields. Accepts title, mode, report_ids, archived."""
        session = await self.get_session(session_id)
        if session is None:
            return None

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.now(UTC)
        await self._db.flush()
        return session

    async def rename_session(self, session_id: str, title: str) -> ChatSessionModel | None:
        """Rename a session."""
        return await self.update_session(session_id, title=title)

    async def archive_session(self, session_id: str) -> ChatSessionModel | None:
        """Archive a session."""
        return await self.update_session(session_id, archived=True)

    async def restore_session(self, session_id: str) -> ChatSessionModel | None:
        """Restore an archived session."""
        return await self.update_session(session_id, archived=False)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its messages. Returns True if deleted."""
        session = await self.get_session(session_id)
        if session is None:
            return False
        await self._db.delete(session)
        await self._db.flush()
        logger.debug("Deleted session %s", session_id)
        return True

    async def list_sessions(
        self,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatSessionModel]:
        """List sessions, newest first."""
        query = select(ChatSessionModel)
        if not include_archived:
            query = query.where(ChatSessionModel.archived == False)  # noqa: E712
        query = query.order_by(ChatSessionModel.updated_at.desc()).limit(limit).offset(offset)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def count_sessions(self, include_archived: bool = False) -> int:
        """Count sessions."""
        query = select(ChatSessionModel)
        if not include_archived:
            query = query.where(ChatSessionModel.archived == False)  # noqa: E712
        result = await self._db.execute(query)
        return len(result.scalars().all())
