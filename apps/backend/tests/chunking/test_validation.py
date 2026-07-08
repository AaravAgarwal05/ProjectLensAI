"""Tests for ValidationEngine."""
import pytest

from src.ai_core.chunking.models import Chunk, ChunkingResult
from src.ai_core.chunking.validation import ValidationEngine


def _chunk(text: str, **kw) -> Chunk:
    return Chunk(text=text, **kw)


class TestValidationEngine:
    def test_valid_result(self):
        engine = ValidationEngine()
        result = ChunkingResult(chunks=[_chunk("Hello world")])
        vr = engine.validate(result)
        assert vr.valid is True
        assert vr.errors == []

    def test_empty_chunk(self):
        engine = ValidationEngine()
        result = ChunkingResult(chunks=[_chunk("")])
        vr = engine.validate(result)
        assert vr.valid is False
        assert len(vr.warnings) > 0

    def test_duplicate_chunks(self):
        engine = ValidationEngine()
        result = ChunkingResult(
            chunks=[_chunk("Duplicate text"), _chunk("Duplicate text")]
        )
        vr = engine.validate(result)
        assert len([w for w in vr.warnings if "duplicate" in w.lower()]) > 0

    def test_oversized_chunk(self):
        engine = ValidationEngine(max_chunk_size=50)
        result = ChunkingResult(chunks=[_chunk("A" * 100)])
        vr = engine.validate(result)
        assert len([w for w in vr.warnings if "exceeds" in w.lower()]) > 0

    def test_tiny_chunk(self):
        engine = ValidationEngine(min_chunk_size=50)
        result = ChunkingResult(
            chunks=[_chunk("A" * 10), _chunk("B" * 100)]
        )
        vr = engine.validate(result)
        assert len([w for w in vr.warnings if "below" in w.lower() or "min" in w.lower()]) > 0

    def test_last_chunk_exempt_from_tiny(self):
        """Last chunk can be short without warning."""
        engine = ValidationEngine(min_chunk_size=50)
        result = ChunkingResult(
            chunks=[_chunk("B" * 100), _chunk("A" * 10)]  # last is short
        )
        vr = engine.validate(result)
        tiny_warnings = [w for w in vr.warnings if "below" in w.lower()]
        assert len(tiny_warnings) == 0

    def test_negative_offset(self):
        engine = ValidationEngine()
        result = ChunkingResult(
            chunks=[_chunk("text", start_offset=-1, end_offset=4)]
        )
        vr = engine.validate(result)
        assert vr.valid is False

    def test_invalid_offset_order(self):
        engine = ValidationEngine()
        result = ChunkingResult(
            chunks=[_chunk("text", start_offset=10, end_offset=5)]
        )
        vr = engine.validate(result)
        assert vr.valid is False

    def test_strict_mode_promotes_warnings(self):
        engine = ValidationEngine(strict=True)
        result = ChunkingResult(chunks=[_chunk("")])
        vr = engine.validate(result)
        assert vr.valid is False
        assert len(vr.errors) > 0
        # Warnings should be empty (promoted to errors)
        assert len([w for w in vr.warnings if "empty" in w.lower()]) == 0

    def test_validate_single_chunk(self):
        engine = ValidationEngine()
        tr = engine.validate_chunk(_chunk("valid text"))
        assert tr.valid is True

    def test_validate_single_chunk_empty(self):
        engine = ValidationEngine()
        tr = engine.validate_chunk(_chunk(""))
        assert tr.valid is False

    def test_missing_page_numbers(self):
        engine = ValidationEngine()
        result = ChunkingResult(chunks=[_chunk("text", page_number=None)])
        vr = engine.validate(result)
        assert len([w for w in vr.warnings if "no page number" in w.lower()]) > 0

    def test_merge_results(self):
        from src.ai_core.chunking.validation import ValidationResult

        v1 = ValidationResult(valid=True)
        v2 = ValidationResult(valid=False, errors=["error"])
        merged = v1.merge(v2)
        assert merged.valid is False
        assert "error" in merged.errors