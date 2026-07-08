"""Tests for VectorStoreValidationEngine."""

from src.ai_core.vector_store.models import VectorDocument, VectorMetadata
from src.ai_core.vector_store.validation import VectorStoreValidationEngine


def _make_doc(
    chunk_id: str,
    vector: list[float] | None = None,
    dimensions: int = 0,
    report_id: str = "",
    version_id: str = "",
) -> VectorDocument:
    if vector is not None:
        vec = vector
        dims = dimensions or len(vec)
    else:
        vec = [0.1, 0.2, 0.3]
        dims = dimensions or len(vec)
    return VectorDocument(
        chunk_id=chunk_id,
        vector=vec,
        dimensions=dims,
        metadata=VectorMetadata(
            chunk_id=chunk_id,
            report_id=report_id,
            version_id=version_id,
        ),
    )


class TestVectorStoreValidationEngine:
    def test_valid_result(self):
        engine = VectorStoreValidationEngine(expected_dimensions=3)
        docs = [
            _make_doc("c1", [0.1, 0.2, 0.3], report_id="r1", version_id="v1"),
            _make_doc("c2", [0.4, 0.5, 0.6], report_id="r1", version_id="v1"),
        ]
        vr = engine.validate_indexing("col", docs)
        assert vr.valid is True
        assert vr.errors == []
        assert vr.warnings == []

    def test_dimension_mismatch(self):
        engine = VectorStoreValidationEngine(expected_dimensions=3)
        docs = [_make_doc("c1", [0.1, 0.2], dimensions=2)]
        vr = engine.validate_indexing("col", docs)
        assert vr.valid is False
        assert len(vr.warnings) > 0
        assert "dimension" in vr.warnings[0].lower()

    def test_duplicate_chunk_ids(self):
        engine = VectorStoreValidationEngine()
        docs = [
            _make_doc("c1", report_id="r1", version_id="v1"),
            _make_doc("c1", report_id="r1", version_id="v1"),
        ]
        vr = engine.validate_indexing("col", docs)
        assert vr.valid is False
        assert any("duplicate" in w.lower() for w in vr.warnings)

    def test_empty_vector(self):
        engine = VectorStoreValidationEngine()
        docs = [_make_doc("c1", vector=[])]
        vr = engine.validate_indexing("col", docs)
        # empty vector + no report_id/version_id → warnings but no NaN/Inf errors
        assert any("empty" in w.lower() for w in vr.warnings)

    def test_nan_values(self):
        engine = VectorStoreValidationEngine()
        docs = [_make_doc("c1", [float("nan"), 0.2, 0.3])]
        vr = engine.validate_indexing("col", docs)
        assert vr.valid is False
        assert any("nan" in w.lower() for w in vr.warnings)

    def test_inf_values(self):
        engine = VectorStoreValidationEngine()
        docs = [_make_doc("c1", [float("inf"), 0.2, 0.3])]
        vr = engine.validate_indexing("col", docs)
        assert vr.valid is False
        assert any("inf" in w.lower() for w in vr.warnings)

    def test_missing_report_id(self):
        engine = VectorStoreValidationEngine()
        docs = [_make_doc("c1", report_id="", version_id="v1")]
        vr = engine.validate_indexing("col", docs)
        assert vr.valid is True  # warnings, not errors
        assert any("report_id" in w for w in vr.warnings)

    def test_missing_version_id(self):
        engine = VectorStoreValidationEngine()
        docs = [_make_doc("c1", report_id="r1", version_id="")]
        vr = engine.validate_indexing("col", docs)
        assert vr.valid is True
        assert any("version_id" in w for w in vr.warnings)

    def test_strict_mode(self):
        engine = VectorStoreValidationEngine(strict=True)
        docs = [_make_doc("c1", report_id="", version_id="")]
        vr = engine.validate_indexing("col", docs)
        assert vr.valid is False
        assert len(vr.errors) > 0
