"""Validation engine for vector-store operations.

Validates:
- Vector dimensions match expected dimensionality.
- No duplicate chunk_ids within a batch.
- Metadata consistency (required fields present).
- No invalid vectors (NaN, inf, empty).
- No missing report_id or version_id.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

from src.ai_core.vector_store.models import VectorDocument

logger = logging.getLogger(__name__)


@dataclass
class IndexValidationResult:
    """Outcome of an index validation pass.

    Attributes:
        valid: ``True`` when no errors.
        errors: Fatal issues.
        warnings: Non-fatal observations.
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class VectorStoreValidationEngine:
    """Validates indexing operations.

    Configured with expected vector dimensions and optional strict mode.
    """

    def __init__(
        self,
        expected_dimensions: int | None = None,
        strict: bool = False,
    ) -> None:
        self._expected_dimensions = expected_dimensions
        self._strict = strict

    def validate_indexing(
        self,
        collection: str,
        documents: list[VectorDocument],
    ) -> IndexValidationResult:
        """Run all checks on *documents* for *collection*."""
        vr = IndexValidationResult()
        self._check_dimensions(documents, vr)
        self._check_duplicate_chunk_ids(documents, vr)
        self._check_invalid_vectors(documents, vr)
        self._check_metadata(documents, vr)

        if self._strict and vr.warnings:
            vr.errors.extend(vr.warnings)
            vr.warnings = []
            vr.valid = False

        return vr

    def _check_dimensions(
        self,
        documents: list[VectorDocument],
        vr: IndexValidationResult,
    ) -> None:
        if self._expected_dimensions is None:
            return
        for i, doc in enumerate(documents):
            if doc.dimensions and doc.dimensions != self._expected_dimensions:
                msg = (
                    f"Document {i} (chunk {doc.chunk_id}) dimension "
                    f"mismatch: expected {self._expected_dimensions}, "
                    f"got {doc.dimensions}"
                )
                vr.warnings.append(msg)
                vr.valid = False
            elif len(doc.vector) != self._expected_dimensions:
                msg = (
                    f"Document {i} (chunk {doc.chunk_id}) vector length "
                    f"mismatch: expected {self._expected_dimensions}, "
                    f"got {len(doc.vector)}"
                )
                vr.warnings.append(msg)
                vr.valid = False

    def _check_duplicate_chunk_ids(
        self,
        documents: list[VectorDocument],
        vr: IndexValidationResult,
    ) -> None:
        seen: set[str] = set()
        for doc in documents:
            if doc.chunk_id in seen:
                msg = f"Duplicate chunk_id: {doc.chunk_id}"
                vr.warnings.append(msg)
                vr.valid = False
            seen.add(doc.chunk_id)

    def _check_invalid_vectors(
        self,
        documents: list[VectorDocument],
        vr: IndexValidationResult,
    ) -> None:
        for i, doc in enumerate(documents):
            if not doc.vector:
                msg = f"Document {i} (chunk {doc.chunk_id}) has empty vector"
                vr.warnings.append(msg)
                vr.valid = False
                continue
            if any(math.isnan(v) for v in doc.vector):
                msg = f"Document {i} (chunk {doc.chunk_id}) contains NaN"
                vr.warnings.append(msg)
                vr.valid = False
            if any(math.isinf(v) for v in doc.vector):
                msg = f"Document {i} (chunk {doc.chunk_id}) contains Inf"
                vr.warnings.append(msg)
                vr.valid = False

    def _check_metadata(
        self,
        documents: list[VectorDocument],
        vr: IndexValidationResult,
    ) -> None:
        for i, doc in enumerate(documents):
            if not doc.metadata.report_id:
                vr.warnings.append(f"Document {i} (chunk {doc.chunk_id}) missing report_id")
            if not doc.metadata.version_id:
                vr.warnings.append(f"Document {i} (chunk {doc.chunk_id}) missing version_id")
