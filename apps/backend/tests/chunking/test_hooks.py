"""Tests for HookRegistry and HookEvent."""
from shared.models import ParsedDocument

from src.ai_core.chunking.hooks import HookEvent, HookRegistry


def _make_doc(text: str = "test") -> ParsedDocument:
    return ParsedDocument(
        report_id="test",
        parser_used="test",
        clean_text=text,
    )


class TestHookRegistry:
    def test_register_and_run_before_chunking(self):
        registry = HookRegistry()
        calls = []

        def hook(doc):
            calls.append("called")
            return doc

        registry.register(HookEvent.BEFORE_CHUNKING, hook, name="test_hook")
        doc = _make_doc()
        result = registry.run_before_chunking(doc)
        assert len(calls) == 1
        assert result is doc

    def test_register_and_run_after_chunking(self):
        registry = HookRegistry()
        calls = []

        def hook(result):
            calls.append("called")
            return result

        registry.register(HookEvent.AFTER_CHUNKING, hook)
        from src.ai_core.chunking.models import ChunkingResult

        result = ChunkingResult()
        returned = registry.run_after_chunking(result)
        assert len(calls) == 1
        assert returned is result

    def test_multiple_hooks_run_in_order(self):
        registry = HookRegistry()
        order = []

        def hook1(doc):
            order.append(1)
            return doc

        def hook2(doc):
            order.append(2)
            return doc

        registry.register(HookEvent.BEFORE_CHUNKING, hook1, name="h1")
        registry.register(HookEvent.BEFORE_CHUNKING, hook2, name="h2")
        registry.run_before_chunking(_make_doc())
        assert order == [1, 2]

    def test_hook_modifies_document(self):
        registry = HookRegistry()

        def add_prefix(doc):
            doc.clean_text = "prefix_" + doc.clean_text
            return doc

        registry.register(HookEvent.BEFORE_CHUNKING, add_prefix, name="prefix")
        doc = _make_doc("original")
        result = registry.run_before_chunking(doc)
        assert result.clean_text == "prefix_original"

    def test_one_shot_hook(self):
        registry = HookRegistry()
        calls = []

        def hook(doc):
            calls.append("called")
            return doc

        registry.register(HookEvent.BEFORE_CHUNKING, hook, once=True)
        registry.run_before_chunking(_make_doc())
        registry.run_before_chunking(_make_doc())
        assert len(calls) == 1

    def test_unregister(self):
        registry = HookRegistry()

        def hook(doc):
            return doc

        registry.register(HookEvent.BEFORE_CHUNKING, hook, name="remove_me")
        assert registry.unregister("remove_me") is True
        assert registry.unregister("remove_me") is False

    def test_list_hooks(self):
        registry = HookRegistry()

        def hook(doc):
            return doc

        registry.register(HookEvent.BEFORE_CHUNKING, hook, name="h1")
        registry.register(HookEvent.AFTER_CHUNKING, hook, name="h2")
        hooks = registry.list_hooks()
        assert len(hooks) == 2

        filtered = registry.list_hooks(HookEvent.BEFORE_CHUNKING)
        assert len(filtered) == 1
        assert filtered[0].name == "h1"

    def test_clear(self):
        registry = HookRegistry()

        def hook(doc):
            return doc

        registry.register(HookEvent.BEFORE_CHUNKING, hook)
        registry.clear()
        assert len(registry.list_hooks()) == 0

    def test_hook_error_does_not_crash(self):
        registry = HookRegistry()

        def failing(doc):
            raise RuntimeError("hook failed")

        registry.register(HookEvent.BEFORE_CHUNKING, failing, name="failing")
        doc = _make_doc()
        result = registry.run_before_chunking(doc)
        assert result is doc

    def test_string_event_name(self):
        registry = HookRegistry()

        def hook(doc):
            return doc

        registry.register("before_chunking", hook)
        assert len(registry.list_hooks(HookEvent.BEFORE_CHUNKING)) == 1