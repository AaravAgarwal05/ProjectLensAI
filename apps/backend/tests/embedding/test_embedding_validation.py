"""Tests for EmbeddingValidationEngine."""

from src.ai_core.embedding.models import EmbeddedChunk, EmbeddingResult, EmbeddingVector
from src.ai_core.embedding.validation import EmbeddingValidationEngine


def _ec(chunk_id: str, vector: list[float], dims: int | None = None) -> EmbeddedChunk:
    return EmbeddedChunk(
        chunk_id=chunk_id,
        vector=EmbeddingVector(vector=vector, dimensions=len(vector)),
        embedding_model="test",
        embedding_provider="test",
        dimensions=dims or len(vector),
    )


class TestEmbeddingValidationEngine:
    def test_valid_result(self):
        engine = EmbeddingValidationEngine()
        result = EmbeddingResult(embeddings=[_ec("1", [0.1, 0.2, 0.3])])
        vr = engine.validate(result)
        assert vr.valid is True

    def test_empty_vector(self):
        engine = EmbeddingValidationEngine()
        result = EmbeddingResult(embeddings=[_ec("1", [])])
        vr = engine.validate(result)
        assert vr.valid is False
        assert any("empty" in w.lower() for w in vr.warnings)

    def test_dimension_mismatch(self):
        engine = EmbeddingValidationEngine(expected_dimensions=3)
        result = EmbeddingResult(embeddings=[_ec("1", [0.1, 0.2])])
        vr = engine.validate(result)
        assert vr.valid is False
        assert any("dimension" in w.lower() for w in vr.warnings)

    def test_nan_values(self):
        engine = EmbeddingValidationEngine()
        result = EmbeddingResult(embeddings=[_ec("1", [0.1, float("nan"), 0.3])])
        vr = engine.validate(result)
        assert vr.valid is False
        assert any("nan" in w.lower() for w in vr.warnings)

    def test_inf_values(self):
        engine = EmbeddingValidationEngine()
        result = EmbeddingResult(embeddings=[_ec("1", [0.1, float("inf"), 0.3])])
        vr = engine.validate(result)
        assert vr.valid is False
        assert any("inf" in w.lower() for w in vr.warnings)

    def test_duplicate_vectors(self):
        engine = EmbeddingValidationEngine()
        result = EmbeddingResult(
            embeddings=[
                _ec("1", [0.1, 0.2, 0.3]),
                _ec("2", [0.1, 0.2, 0.3]),
            ]
        )
        vr = engine.validate(result)
        assert any("duplicate" in w.lower() for w in vr.warnings)

    def test_unique_vectors(self):
        engine = EmbeddingValidationEngine()
        result = EmbeddingResult(
            embeddings=[
                _ec("1", [0.1, 0.2, 0.3]),
                _ec("2", [0.4, 0.5, 0.6]),
            ]
        )
        vr = engine.validate(result)
        assert vr.valid is True

    def test_strict_mode(self):
        engine = EmbeddingValidationEngine(strict=True)
        result = EmbeddingResult(embeddings=[_ec("1", [])])
        vr = engine.validate(result)
        assert vr.valid is False
        assert len(vr.errors) > 0

    def test_validate_single_chunk(self):
        engine = EmbeddingValidationEngine()
        vr = engine.validate_embedded_chunk(_ec("1", [0.1, 0.2]))
        assert vr.valid is True

    def test_validate_single_chunk_nan(self):
        engine = EmbeddingValidationEngine()
        vr = engine.validate_embedded_chunk(_ec("1", [0.1, float("nan")]))
        assert vr.valid is False

    def test_merge_results(self):
        from src.ai_core.embedding.validation import EmbeddingValidationResult

        v1 = EmbeddingValidationResult(valid=True)
        v2 = EmbeddingValidationResult(valid=False, errors=["error"])
        merged = v1.merge(v2)
        assert merged.valid is False
        assert "error" in merged.errors
