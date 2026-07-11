"""Tests for context hook system."""

import pytest

from src.ai_core.context.hooks import ContextHookEvent, ContextHookRegistry
from src.ai_core.context.models import LLMContext


class TestContextHookRegistry:
    def test_register_and_list(self):
        reg = ContextHookRegistry()

        async def hook1(q, c, h):
            return q, c, h

        async def hook2(ctx):
            return ctx

        reg.register(ContextHookEvent.BEFORE_CONTEXT, hook1, name="h1")
        reg.register(ContextHookEvent.AFTER_CONTEXT, hook2, name="h2")

        hooks = reg.list_hooks()
        assert len(hooks) == 2

    def test_unregister(self):
        reg = ContextHookRegistry()

        async def hook(q, c, h):
            return q, c, h

        reg.register(ContextHookEvent.BEFORE_CONTEXT, hook, name="h1")
        assert reg.unregister("h1") is True
        assert reg.unregister("nonexistent") is False

    @pytest.mark.asyncio
    async def test_run_before_context(self):
        reg = ContextHookRegistry()

        async def add_tag(query, chunks, history):
            return f"[tagged] {query}", chunks, history

        reg.register(ContextHookEvent.BEFORE_CONTEXT, add_tag, name="tag")
        q, c, h = await reg.run_before_context("hello", [], [])
        assert "[tagged]" in q

    @pytest.mark.asyncio
    async def test_run_after_context(self):
        reg = ContextHookRegistry()

        async def add_warning(ctx: LLMContext) -> LLMContext:
            ctx.warnings.append("check done")
            return ctx

        reg.register(ContextHookEvent.AFTER_CONTEXT, add_warning, name="warn")
        ctx = LLMContext()
        result = await reg.run_after_context(ctx)
        assert any("check done" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_run_before_budget(self):
        reg = ContextHookRegistry()

        async def set_budget(ctx: LLMContext) -> LLMContext:
            ctx.budget.total = 4096
            return ctx

        reg.register(ContextHookEvent.BEFORE_BUDGET, set_budget, name="budget")
        ctx = LLMContext()
        result = await reg.run_before_budget(ctx)
        assert result.budget.total == 4096

    @pytest.mark.asyncio
    async def test_hook_error_doesnt_break(self):
        reg = ContextHookRegistry()

        async def broken(q, c, h):
            raise ValueError("oops")

        async def fine(q, c, h):
            return "fixed", c, h

        reg.register(ContextHookEvent.BEFORE_CONTEXT, broken, name="broken")
        reg.register(ContextHookEvent.BEFORE_CONTEXT, fine, name="fine")
        q, c, h = await reg.run_before_context("test", [], [])
        assert q == "fixed"

    @pytest.mark.asyncio
    async def test_once_hook(self):
        reg = ContextHookRegistry()
        call_count = 0

        async def once(q, c, h):
            nonlocal call_count
            call_count += 1
            return q, c, h

        reg.register(ContextHookEvent.BEFORE_CONTEXT, once, name="once", once=True)
        await reg.run_before_context("a", [], [])
        await reg.run_before_context("b", [], [])
        assert call_count == 1

    def test_clear(self):
        reg = ContextHookRegistry()

        async def hook(q, c, h):
            return q, c, h

        reg.register(ContextHookEvent.BEFORE_CONTEXT, hook)
        reg.clear()
        assert len(reg.list_hooks()) == 0

    def test_list_by_event(self):
        reg = ContextHookRegistry()

        async def hook1(q, c, h):
            return q, c, h

        async def hook2(ctx):
            return ctx

        reg.register(ContextHookEvent.BEFORE_CONTEXT, hook1, name="h1")
        reg.register(ContextHookEvent.AFTER_CONTEXT, hook2, name="h2")

        before = reg.list_hooks(ContextHookEvent.BEFORE_CONTEXT)
        assert len(before) == 1
        assert before[0].name == "h1"
