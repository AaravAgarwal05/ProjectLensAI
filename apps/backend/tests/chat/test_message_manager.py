"""Tests for MessageManager."""

from __future__ import annotations

import pytest

from src.ai_core.chat.message_manager import MessageManager
from src.ai_core.chat.session_manager import SessionManager

pytest_plugins = ["tests.chat.fixtures"]


class TestMessageManager:
    @pytest.mark.asyncio
    async def test_create_message(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        msg = await message_manager.create_message(
            session_id=session.id,
            role="user",
            content="Hello",
        )
        assert msg.id is not None
        assert msg.session_id == session.id
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.citations == []
        assert msg.msg_metadata == {}

    @pytest.mark.asyncio
    async def test_get_message(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        created = await message_manager.create_message(session.id, "user", "Test")
        retrieved = await message_manager.get_message(created.id)
        assert retrieved is not None
        assert retrieved.content == "Test"

    @pytest.mark.asyncio
    async def test_get_message_not_found(self, message_manager: MessageManager):
        msg = await message_manager.get_message("nonexistent")
        assert msg is None

    @pytest.mark.asyncio
    async def test_edit_message(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        created = await message_manager.create_message(session.id, "user", "Original")
        edited = await message_manager.edit_message(created.id, "Edited")
        assert edited is not None
        assert edited.content == "Edited"

    @pytest.mark.asyncio
    async def test_delete_message(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        created = await message_manager.create_message(session.id, "user", "Delete")
        deleted = await message_manager.delete_message(created.id)
        assert deleted is True
        assert await message_manager.get_message(created.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_message(self, message_manager: MessageManager):
        deleted = await message_manager.delete_message("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_messages(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        for i in range(3):
            await message_manager.create_message(session.id, "user", f"Message {i}")

        msgs = await message_manager.list_messages(session.id)
        assert len(msgs) == 3
        assert msgs[0].content == "Message 0"
        assert msgs[-1].content == "Message 2"

    @pytest.mark.asyncio
    async def test_list_messages_pagination(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        for i in range(5):
            await message_manager.create_message(session.id, "user", f"Msg {i}")

        page1 = await message_manager.list_messages(session.id, limit=2)
        assert len(page1) == 2

        page2 = await message_manager.list_messages(session.id, limit=2, offset=2)
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_list_messages_before_id(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        msgs = []
        for i in range(3):
            m = await message_manager.create_message(session.id, "user", f"Msg {i}")
            msgs.append(m)

        # List messages before the last one
        before = await message_manager.list_messages(session.id, before_id=msgs[-1].id)
        assert len(before) == 2
        assert before[0].content == "Msg 0"
        assert before[-1].content == "Msg 1"

    @pytest.mark.asyncio
    async def test_count_messages(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        assert await message_manager.count_messages(session.id) == 0

        await message_manager.create_message(session.id, "user", "A")
        await message_manager.create_message(session.id, "assistant", "B")
        assert await message_manager.count_messages(session.id) == 2

    @pytest.mark.asyncio
    async def test_delete_all_messages(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
    ):
        session = await session_manager.create_session()
        for i in range(3):
            await message_manager.create_message(session.id, "user", f"M{i}")

        deleted = await message_manager.delete_all_messages(session.id)
        assert deleted == 3
        assert await message_manager.count_messages(session.id) == 0
