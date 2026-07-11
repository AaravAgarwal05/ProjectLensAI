"""Tests for retrieval hook system."""

from src.ai_core.retrieval.hooks import RetrievalHookEvent, RetrievalHookRegistry
from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk, SearchQuery


class TestRetrievalHookRegistry:
    def test_register_and_list(self):
        reg = RetrievalHookRegistry()

        async def hook1(q: SearchQuery) -> SearchQuery:
            return q

        async def hook2(c: list) -> list:
            return c

        reg.register(RetrievalHookEvent.BEFORE_RETRIEVAL, hook1, name="h1")
        reg.register(RetrievalHookEvent.AFTER_RETRIEVAL, hook2, name="h2")

        hooks = reg.list_hooks()
        assert len(hooks) == 2
        assert hooks[0].name == "h1"
        assert hooks[1].name == "h2"

    def test_unregister(self):
        reg = RetrievalHookRegistry()

        async def hook(q: SearchQuery) -> SearchQuery:
            return q

        reg.register(RetrievalHookEvent.BEFORE_RETRIEVAL, hook, name="h1")
        assert reg.unregister("h1") is True
        assert reg.unregister("nonexistent") is False

    async def test_run_before_retrieval(self):
        reg = RetrievalHookRegistry()

        async def add_tag(q: SearchQuery) -> SearchQuery:
            q.text = f"[tagged] {q.text}"
            return q

        reg.register(RetrievalHookEvent.BEFORE_RETRIEVAL, add_tag, name="tag")
        query = SearchQuery(text="hello")
        result = await reg.run_before_retrieval(query)
        assert "[tagged]" in result.text

    async def test_run_after_retrieval(self):
        reg = RetrievalHookRegistry()
        chunks = [RetrievedChunk(chunk_id="c1", content="a", score=0.5)]

        async def filter_low(chunks_list: list) -> list:
            return [c for c in chunks_list if c.score > 0.6]

        reg.register(RetrievalHookEvent.AFTER_RETRIEVAL, filter_low, name="filter")
        result = await reg.run_after_retrieval(chunks)
        assert len(result) == 0

    async def test_run_before_reranking(self):
        reg = RetrievalHookRegistry()

        async def boost(q: list) -> list:
            for c in q:
                c.score += 0.1
            return q

        reg.register(RetrievalHookEvent.BEFORE_RERANKING, boost, name="boost")
        chunks = [RetrievedChunk(chunk_id="c1", content="a", score=0.5)]
        result = await reg.run_before_reranking(chunks)
        assert result[0].score == 0.6

    async def test_run_after_reranking(self):
        reg = RetrievalHookRegistry()

        async def add_warning(r: RetrievalResult) -> RetrievalResult:
            r.warnings.append("post-rerank check done")
            return r

        reg.register(RetrievalHookEvent.AFTER_RERANKING, add_warning, name="warn")
        result = RetrievalResult()
        out = await reg.run_after_reranking(result)
        assert any("post-rerank" in w for w in out.warnings)

    async def test_once_hook(self):
        reg = RetrievalHookRegistry()
        call_count = 0

        async def once(q: SearchQuery) -> SearchQuery:
            nonlocal call_count
            call_count += 1
            return q

        reg.register(RetrievalHookEvent.BEFORE_RETRIEVAL, once, name="once", once=True)
        await reg.run_before_retrieval(SearchQuery(text="a"))
        await reg.run_before_retrieval(SearchQuery(text="b"))
        assert call_count == 1  # only fired once

    async def test_hook_error_doesnt_break(self):
        reg = RetrievalHookRegistry()

        async def broken(q: SearchQuery) -> SearchQuery:
            raise ValueError("oops")

        async def fine(q: SearchQuery) -> SearchQuery:
            q.text = "fixed"
            return q

        reg.register(RetrievalHookEvent.BEFORE_RETRIEVAL, broken, name="broken")
        reg.register(RetrievalHookEvent.BEFORE_RETRIEVAL, fine, name="fine")
        query = await reg.run_before_retrieval(SearchQuery(text="test"))
        assert query.text == "fixed"

    def test_clear(self):
        reg = RetrievalHookRegistry()

        async def hook(q: SearchQuery) -> SearchQuery:
            return q

        reg.register(RetrievalHookEvent.BEFORE_RETRIEVAL, hook)
        reg.clear()
        assert len(reg.list_hooks()) == 0
