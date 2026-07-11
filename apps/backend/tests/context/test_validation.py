"""Tests for context validation engine."""

from src.ai_core.context.models import ContextBudget, ContextChunk, LLMContext
from src.ai_core.context.validation import ContextValidationEngine


def _make_chunk(chunk_id: str, source_id: str = "", content: str = "content"):
    return ContextChunk(chunk_id=chunk_id, content=content, source_id=source_id)


class TestContextValidationEngine:
    def test_valid_context(self):
        engine = ContextValidationEngine()
        ctx = LLMContext(
            query="test",
            chunks=[_make_chunk("c1", "src1")],
            budget=ContextBudget(total=1000, system_prompt=100),
        )
        vr = engine.validate(ctx)
        assert vr.valid is True

    def test_empty_context_warning(self):
        engine = ContextValidationEngine()
        ctx = LLMContext(query="test")
        vr = engine.validate(ctx)
        assert any("Empty" in w for w in vr.warnings)

    def test_empty_context_strict(self):
        engine = ContextValidationEngine(strict=True)
        ctx = LLMContext(query="")
        vr = engine.validate(ctx)
        assert vr.valid is False

    def test_duplicate_chunks(self):
        engine = ContextValidationEngine()
        ctx = LLMContext(
            query="test",
            chunks=[_make_chunk("c1"), _make_chunk("c1")],
            budget=ContextBudget(total=1000, system_prompt=100),
        )
        vr = engine.validate(ctx)
        assert any("Duplicate" in w for w in vr.warnings)

    def test_missing_source_id(self):
        engine = ContextValidationEngine()
        ctx = LLMContext(
            query="test",
            chunks=[_make_chunk("c1", source_id="")],
            budget=ContextBudget(total=1000, system_prompt=100),
        )
        vr = engine.validate(ctx)
        assert any("missing source_id" in w.lower() for w in vr.warnings)

    def test_broken_citations(self):
        engine = ContextValidationEngine()
        chunks = [
            ContextChunk(chunk_id="c1", content="x", citations=["parent:p2"]),
        ]
        ctx = LLMContext(
            query="test",
            chunks=chunks,
            budget=ContextBudget(total=1000, system_prompt=100),
        )
        vr = engine.validate(ctx)
        assert any("broken parent" in w.lower() for w in vr.warnings)

    def test_zero_budget(self):
        engine = ContextValidationEngine()
        ctx = LLMContext(query="test", budget=ContextBudget())
        vr = engine.validate(ctx)
        assert vr.valid is False
        assert any("zero" in e.lower() for e in vr.errors)

    def test_budget_exceeded(self):
        engine = ContextValidationEngine()
        ctx = LLMContext(
            query="test",
            budget=ContextBudget(total=100, system_prompt=500),
        )
        vr = engine.validate(ctx)
        assert any("exceeded" in w.lower() for w in vr.warnings)

    def test_empty_chunk_content(self):
        engine = ContextValidationEngine()
        ctx = LLMContext(
            query="test",
            chunks=[_make_chunk("c1", content="")],
            budget=ContextBudget(total=1000, system_prompt=100),
        )
        vr = engine.validate(ctx)
        assert vr.valid is False
        assert any("empty" in e.lower() for e in vr.errors)
