"""Tests for SessionManager."""

from __future__ import annotations

import pytest

from src.ai_core.chat.session_manager import SessionManager

pytest_plugins = ["tests.chat.fixtures"]


class TestSessionManager:
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager: SessionManager):
        session = await session_manager.create_session(
            title="Test Session",
            report_ids=["r1"],
            mode="single",
        )
        assert session.id is not None
        assert session.title == "Test Session"
        assert session.report_ids == ["r1"]
        assert session.mode == "single"
        assert session.archived is False

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager: SessionManager):
        created = await session_manager.create_session(title="Get Test")
        retrieved = await session_manager.get_session(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Get Test"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager: SessionManager):
        session = await session_manager.get_session("nonexistent")
        assert session is None

    @pytest.mark.asyncio
    async def test_rename_session(self, session_manager: SessionManager):
        created = await session_manager.create_session(title="Original")
        updated = await session_manager.rename_session(created.id, "Renamed")
        assert updated is not None
        assert updated.title == "Renamed"

    @pytest.mark.asyncio
    async def test_archive_restore_session(self, session_manager: SessionManager):
        created = await session_manager.create_session(title="Archive Test")
        # Archive
        archived = await session_manager.archive_session(created.id)
        assert archived is not None
        assert archived.archived is True
        # Restore
        restored = await session_manager.restore_session(created.id)
        assert restored is not None
        assert restored.archived is False

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager: SessionManager):
        created = await session_manager.create_session(title="Delete Me")
        deleted = await session_manager.delete_session(created.id)
        assert deleted is True
        # Verify gone
        retrieved = await session_manager.get_session(created.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, session_manager: SessionManager):
        deleted = await session_manager.delete_session("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_manager: SessionManager):
        await session_manager.create_session(title="A")
        await session_manager.create_session(title="B")
        sessions = await session_manager.list_sessions()
        assert len(sessions) >= 2

    @pytest.mark.asyncio
    async def test_list_sessions_excludes_archived(self, session_manager: SessionManager):
        await session_manager.create_session(title="Active")
        s2 = await session_manager.create_session(title="Archived")
        await session_manager.archive_session(s2.id)

        active = await session_manager.list_sessions(include_archived=False)
        assert all(not s.archived for s in active)

        all_sessions = await session_manager.list_sessions(include_archived=True)
        assert len(all_sessions) >= len(active)

    @pytest.mark.asyncio
    async def test_list_sessions_pagination(self, session_manager: SessionManager):
        for i in range(5):
            await session_manager.create_session(title=f"Session {i}")

        page1 = await session_manager.list_sessions(limit=2, offset=0)
        assert len(page1) == 2

        page2 = await session_manager.list_sessions(limit=2, offset=2)
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_count_sessions(self, session_manager: SessionManager):
        count_before = await session_manager.count_sessions()
        await session_manager.create_session(title="Count Test")
        count_after = await session_manager.count_sessions()
        assert count_after == count_before + 1

    @pytest.mark.asyncio
    async def test_update_session(self, session_manager: SessionManager):
        created = await session_manager.create_session(title="Update")
        updated = await session_manager.update_session(created.id, mode="multi")
        assert updated is not None
        assert updated.mode == "multi"
