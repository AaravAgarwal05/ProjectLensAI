"""Tests for ConversationManager."""

from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.conversation import ConversationManager
from src.ai_core.context.models import ConversationMessage


class TestConversationManager:
    def test_empty_history(self):
        mgr = ConversationManager()
        trimmed, summary = mgr.prepare([])
        assert trimmed == []
        assert summary is None

    def test_history_within_limit(self):
        mgr = ConversationManager()
        history = [
            ConversationMessage(role="user", content="hello"),
            ConversationMessage(role="assistant", content="hi there"),
        ]
        trimmed, summary = mgr.prepare(history)
        assert len(trimmed) == 2
        assert summary is None

    def test_history_trimming(self):
        mgr = ConversationManager(
            config=ContextConfiguration(conversation_max_messages=5, max_history_tokens=20)
        )
        history = [ConversationMessage(role="user", content="a" * 50) for _ in range(10)]
        trimmed, summary = mgr.prepare(history)
        # At least 10 msgs exist but only 5 fit by count, then only 1 fits by token budget
        assert len(trimmed) < 10

    def test_summary_generated(self):
        mgr = ConversationManager(
            config=ContextConfiguration(
                conversation_max_messages=2,
                enable_conversation_summary=True,
            )
        )
        history = [
            ConversationMessage(role="user", content=f"long message number {i}") for i in range(10)
        ]
        trimmed, summary = mgr.prepare(history)
        assert summary is not None
        assert summary.text != ""
        assert summary.message_count > 0

    def test_summary_disabled(self):
        mgr = ConversationManager(
            config=ContextConfiguration(
                conversation_max_messages=2,
                enable_conversation_summary=False,
            )
        )
        history = [ConversationMessage(role="user", content=f"msg {i}") for i in range(10)]
        trimmed, summary = mgr.prepare(history)
        assert summary is None

    def test_configure(self):
        mgr = ConversationManager()
        mgr.configure({"max_history_tokens": 1000})
        assert mgr.config.max_history_tokens == 1000
