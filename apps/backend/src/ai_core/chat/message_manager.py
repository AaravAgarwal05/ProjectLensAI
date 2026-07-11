"""Message Manager — CRUD operations for chat messages."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.chat.database import ChatMessageModel

logger = logging.getLogger(__name__)


class MessageManager:
    """Manages chat message lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMessageModel:
        """Create a message in a session."""
        msg = ChatMessageModel(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations or [],
            msg_metadata=metadata or {},
        )
        self._db.add(msg)
        await self._db.flush()
        logger.debug("Created message %s in session %s", msg.id, session_id)
        return msg

    async def get_message(self, message_id: str) -> ChatMessageModel | None:
        """Get a message by ID."""
        result = await self._db.execute(
            select(ChatMessageModel).where(ChatMessageModel.id == message_id)
        )
        return result.scalar_one_or_none()

    async def edit_message(self, message_id: str, content: str) -> ChatMessageModel | None:
        """Edit a message's content."""
        msg = await self.get_message(message_id)
        if msg is None:
            return None
        msg.content = content
        await self._db.flush()
        return msg

    async def delete_message(self, message_id: str) -> bool:
        """Delete a message. Returns True if deleted."""
        msg = await self.get_message(message_id)
        if msg is None:
            return False
        await self._db.delete(msg)
        await self._db.flush()
        return True

    async def list_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        before_id: str | None = None,
    ) -> list[ChatMessageModel]:
        """List messages in a session, oldest first."""
        query = select(ChatMessageModel).where(ChatMessageModel.session_id == session_id)
        if before_id:
            before_msg = await self.get_message(before_id)
            if before_msg:
                query = query.where(ChatMessageModel.created_at < before_msg.created_at)
        query = query.order_by(ChatMessageModel.created_at.asc()).limit(limit).offset(offset)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def count_messages(self, session_id: str) -> int:
        """Count messages in a session."""
        result = await self._db.execute(
            select(func.count(ChatMessageModel.id)).where(ChatMessageModel.session_id == session_id)
        )
        return result.scalar() or 0

    async def delete_all_messages(self, session_id: str) -> int:
        """Delete all messages in a session. Returns count deleted."""
        result = await self._db.execute(
            delete(ChatMessageModel).where(ChatMessageModel.session_id == session_id)
        )
        await self._db.flush()
        rowcount = result.rowcount  # type: ignore[attr-defined]
        return rowcount if rowcount is not None else 0
