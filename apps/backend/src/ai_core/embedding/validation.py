"""Validation engine for embedding results.

Validates embedded chunks produced by any provider.  Checks:

1. **Empty vectors** — zero-length vector.
2. **Dimension mismatch** — vectors don't match expected dimensions.
3. **NaN values** — any float is NaN.
4. **Infinite values** — any float is inf or -inf.
5. **Duplicate vectors** — exact vector duplicates (within tolerance).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

from src.ai_core.embedding.models import EmbeddedChunk, EmbeddingResult

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingValidationResult:
    """Outcome of a validation pass.

    Attributes:
        valid: ``True`` when no errors and only acceptable warnings.
        errors: Fatal issues that should reject the result.
        warnings: Non-fatal observations.
        chunk_errors: Per-chunk-index to error message mapping.
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    chunk_errors: dict[int, str] = field(default_factory=dict)

    def merge(self, other: EmbeddingValidationResult) -> EmbeddingValidationResult:
        """Combine two validation results."""
        return EmbeddingValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            chunk_errors={**self.chunk_errors, **other.chunk_errors},
        )


class EmbeddingValidationEngine:
    """Validates embedded chunks.

    Configured with expected dimensions and optional strict mode.
    """

    def __init__(
        self,
        expected_dimensions: int | None = None,
        strict: bool = False,
        duplicate_tolerance: float = 1e-6,
    ) -> None:
        """Initialize the validation engine.

        Args:
            expected_dimensions: Expected vector dimensionality.
            strict: When ``True``, warnings become errors.
            duplicate_tolerance: Max L2 distance for dedup detection.
        """
        self._expected_dimensions = expected_dimensions
        self._strict = strict
        self._tolerance = duplicate_tolerance

        self._checks = {
            "empty": self._check_empty,
            "dimensions": self._check_dimensions,
            "nan": self._check_nan,
            "inf": self._check_inf,
            "duplicates": self._check_duplicates,
        }

    def validate(self, result: EmbeddingResult) -> EmbeddingValidationResult:
        """Run all checks on *result*."""
        overall = EmbeddingValidationResult()
        for name, check in self._checks.items():
            try:
                vr = check(result)
                overall = overall.merge(vr)
            except Exception:
                logger.exception("Validation check '%s' failed", name)
                overall.errors.append(f"Validation check '{name}' raised an exception")
                overall.valid = False

        if self._strict and overall.warnings:
            overall.errors.extend(overall.warnings)
            overall.warnings = []
            overall.valid = False

        return overall

    def validate_embedded_chunk(self, chunk: EmbeddedChunk) -> EmbeddingValidationResult:
        """Run checks on a single embedded chunk."""
        vr = EmbeddingValidationResult()

        # Empty vector
        if not chunk.vector.vector or len(chunk.vector.vector) == 0:
            vr.warnings.append(f"Chunk {chunk.chunk_id} has empty vector")
            vr.valid = False
            return vr

        # NaN
        if any(math.isnan(v) for v in chunk.vector.vector):
            vr.warnings.append(f"Chunk {chunk.chunk_id} contains NaN values")
            vr.valid = False

        # Inf
        if any(math.isinf(v) for v in chunk.vector.vector):
            vr.warnings.append(f"Chunk {chunk.chunk_id} contains infinite values")
            vr.valid = False

        return vr

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_empty(self, result: EmbeddingResult) -> EmbeddingValidationResult:
        vr = EmbeddingValidationResult()
        for i, emb in enumerate(result.embeddings):
            if not emb.vector.vector or len(emb.vector.vector) == 0:
                msg = f"Embedding {i} (chunk {emb.chunk_id}) has empty vector"
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
                vr.valid = False
        return vr

    def _check_dimensions(self, result: EmbeddingResult) -> EmbeddingValidationResult:
        vr = EmbeddingValidationResult()
        expected = self._expected_dimensions
        for i, emb in enumerate(result.embeddings):
            actual = len(emb.vector.vector)
            if expected is not None and actual != expected:
                msg = (
                    f"Embedding {i} (chunk {emb.chunk_id}) dimension mismatch: "
                    f"expected {expected}, got {actual}"
                )
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
                vr.valid = False
        return vr

    def _check_nan(self, result: EmbeddingResult) -> EmbeddingValidationResult:
        vr = EmbeddingValidationResult()
        for i, emb in enumerate(result.embeddings):
            if any(math.isnan(v) for v in emb.vector.vector):
                msg = f"Embedding {i} (chunk {emb.chunk_id}) contains NaN values"
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
                vr.valid = False
        return vr

    def _check_inf(self, result: EmbeddingResult) -> EmbeddingValidationResult:
        vr = EmbeddingValidationResult()
        for i, emb in enumerate(result.embeddings):
            if any(math.isinf(v) for v in emb.vector.vector):
                msg = f"Embedding {i} (chunk {emb.chunk_id}) contains infinite values"
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
                vr.valid = False
        return vr

    def _check_duplicates(self, result: EmbeddingResult) -> EmbeddingValidationResult:
        vr = EmbeddingValidationResult()
        seen: list[tuple[str, list[float]]] = []
        for i, emb in enumerate(result.embeddings):
            for j, (other_id, other_vec) in enumerate(seen):
                if self._vectors_equal(emb.vector.vector, other_vec):
                    msg = (
                        f"Embedding {i} (chunk {emb.chunk_id}) is a duplicate "
                        f"of embedding {j} (chunk {other_id})"
                    )
                    vr.chunk_errors[i] = msg
                    vr.warnings.append(msg)
                    break
            seen.append((emb.chunk_id, emb.vector.vector))
        return vr

    def _vectors_equal(self, a: list[float], b: list[float]) -> bool:
        """Check if two vectors are equal within tolerance."""
        if len(a) != len(b):
            return False
        return all(abs(va - vb) <= self._tolerance for va, vb in zip(a, b, strict=False))
