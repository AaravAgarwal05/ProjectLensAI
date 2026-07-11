"""Validation engine for retrieval results.

Validates:
- Empty results
- Duplicate chunks (by chunk_id)
- Invalid scores (NaN, Inf, out of range)
- Invalid metadata (missing required fields)
- Score ordering (must be descending)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk


@dataclass
class RetrievalValidationResult:
    """Outcome of a retrieval validation pass."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class RetrievalValidationEngine:
    """Validates retrieval results.

    Configured with optional strict mode.
    """

    def __init__(self, strict: bool = False) -> None:
        self._strict = strict

    def validate_result(self, result: RetrievalResult) -> RetrievalValidationResult:
        """Run all checks on *result*."""
        vr = RetrievalValidationResult()

        if not result.chunks:
            vr.warnings.append("Empty result set — no chunks returned")
            if self._strict:
                vr.errors.append("Empty result set")
                vr.valid = False
            return vr

        self._check_duplicates(result.chunks, vr)
        self._check_scores(result.chunks, vr)
        self._check_ordering(result.chunks, vr)
        self._check_metadata(result.chunks, vr)

        if self._strict and vr.warnings and not vr.errors:
            vr.errors.extend(vr.warnings)
            vr.warnings = []
            vr.valid = False

        return vr

    def _check_duplicates(
        self, chunks: list[RetrievedChunk], vr: RetrievalValidationResult
    ) -> None:
        seen: set[str] = set()
        for c in chunks:
            if c.chunk_id in seen:
                vr.warnings.append(f"Duplicate chunk_id: {c.chunk_id}")
                vr.valid = False
            seen.add(c.chunk_id)

    def _check_scores(self, chunks: list[RetrievedChunk], vr: RetrievalValidationResult) -> None:
        for c in chunks:
            if math.isnan(c.score):
                vr.errors.append(f"Chunk {c.chunk_id} has NaN score")
                vr.valid = False
            if math.isinf(c.score):
                vr.errors.append(f"Chunk {c.chunk_id} has Inf score")
                vr.valid = False
            if c.score < 0.0 or c.score > 1.0:
                vr.warnings.append(f"Chunk {c.chunk_id} score {c.score} outside [0, 1]")

    def _check_ordering(self, chunks: list[RetrievedChunk], vr: RetrievalValidationResult) -> None:
        for i in range(1, len(chunks)):
            if chunks[i].score > chunks[i - 1].score + 1e-9:
                vr.warnings.append(
                    f"Chunk ordering violation at index {i}: "
                    f"{chunks[i].score} > {chunks[i - 1].score}"
                )
                vr.valid = False

    def _check_metadata(self, chunks: list[RetrievedChunk], vr: RetrievalValidationResult) -> None:
        for c in chunks:
            if not c.chunk_id:
                vr.warnings.append("Chunk with empty chunk_id")
            if not c.content and not c.metadata:
                vr.warnings.append(f"Chunk {c.chunk_id} has no content and no metadata")
