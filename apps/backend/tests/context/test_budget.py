"""Tests for TokenBudgetManager."""

from src.ai_core.context.budget import TokenBudgetManager, estimate_tokens
from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import ContextChunk, ConversationMessage


class TestEstimateTokens:
    def test_empty(self):
        assert estimate_tokens("") == 0

    def test_rough(self):
        assert estimate_tokens("hello world") == 2  # 10 chars / 4


class TestTokenBudgetManager:
    def test_allocate_defaults(self):
        mgr = TokenBudgetManager()
        budget = mgr.allocate(
            query="test query",
            chunks=[ContextChunk(chunk_id="c1", content="some content")],
            history=[],
        )
        assert budget.total == 8192
        assert budget.system_prompt == 500
        assert budget.user_query > 0
        assert budget.retrieved_chunks > 0

    def test_allocate_with_history(self):
        mgr = TokenBudgetManager()
        budget = mgr.allocate(
            query="q",
            chunks=[],
            history=[
                ConversationMessage(role="user", content="hello world"),
            ],
        )
        assert budget.conversation_history > 0

    def test_enforce_fits(self):
        mgr = TokenBudgetManager()
        chunks = [
            ContextChunk(chunk_id="c1", content="short", token_count=1),
            ContextChunk(chunk_id="c2", content="short", token_count=1),
        ]
        budget = mgr.allocate(query="q", chunks=chunks, history=[])
        result = mgr.enforce(budget, chunks)
        assert len(result) == 2

    def test_enforce_trims(self):
        mgr = TokenBudgetManager(config=ContextConfiguration(max_tokens=512, max_chunk_tokens=50))
        long_content = "word " * 500
        chunks = [
            ContextChunk(chunk_id="c1", content=long_content, token_count=500),
            ContextChunk(chunk_id="c2", content="more", token_count=10),
        ]
        budget = mgr.allocate(query="q", chunks=chunks, history=[])
        result = mgr.enforce(budget, chunks)
        # Should only fit at most 1 chunk
        assert len(result) <= 1

    def test_enforce_empty(self):
        mgr = TokenBudgetManager()
        assert mgr.enforce(mgr.allocate("q", [], []), []) == []

    def test_configure(self):
        mgr = TokenBudgetManager()
        mgr.configure({"max_tokens": 4096})
        assert mgr.config.max_tokens == 4096
