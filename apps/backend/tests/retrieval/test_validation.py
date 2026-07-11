"""Tests for retrieval validation engine."""

import pytest

from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk
from src.ai_core.retrieval.validation import RetrievalValidationEngine


def _make_chunk(chunk_id: str, score: float = 0.5, content: str = "content") -> RetrievedChunk:
    return RetrievedChunk(chunk_id=chunk_id, content=content, score=score)


class TestRetrievalValidationEngine:
    @pytest.fixture
    def engine(self):
        return RetrievalValidationEngine()

    def test_valid_result(self, engine):
        result = RetrievalResult(
            chunks=[
                _make_chunk("c1", 0.9),
                _make_chunk("c2", 0.8),
                _make_chunk("c3", 0.7),
            ]
        )
        vr = engine.validate_result(result)
        assert vr.valid is True
        assert vr.errors == []

    def test_empty_result(self, engine):
        result = RetrievalResult(chunks=[])
        vr = engine.validate_result(result)
        assert vr.valid is True  # warnings, not errors
        assert any("Empty" in w for w in vr.warnings)

    def test_empty_result_strict(self):
        engine = RetrievalValidationEngine(strict=True)
        result = RetrievalResult(chunks=[])
        vr = engine.validate_result(result)
        assert vr.valid is False

    def test_duplicate_chunks(self, engine):
        result = RetrievalResult(
            chunks=[
                _make_chunk("c1", 0.9),
                _make_chunk("c1", 0.8),
            ]
        )
        vr = engine.validate_result(result)
        assert vr.valid is False
        assert any("duplicate" in w.lower() for w in vr.warnings)

    def test_nan_score(self, engine):
        result = RetrievalResult(chunks=[_make_chunk("c1", float("nan"))])
        vr = engine.validate_result(result)
        assert vr.valid is False
        assert any("NaN" in e for e in vr.errors)

    def test_inf_score(self, engine):
        result = RetrievalResult(chunks=[_make_chunk("c1", float("inf"))])
        vr = engine.validate_result(result)
        assert vr.valid is False
        assert any("Inf" in e for e in vr.errors)

    def test_ordering_violation(self, engine):
        result = RetrievalResult(
            chunks=[
                _make_chunk("c1", 0.5),
                _make_chunk("c2", 0.9),
            ]
        )
        vr = engine.validate_result(result)
        assert vr.valid is False
        assert any("ordering" in w.lower() for w in vr.warnings)

    def test_score_out_of_range(self, engine):
        result = RetrievalResult(chunks=[_make_chunk("c1", 1.5)])
        vr = engine.validate_result(result)
        assert any("outside" in w.lower() for w in vr.warnings)
