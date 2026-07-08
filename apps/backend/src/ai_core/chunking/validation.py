"""Validation engine for chunking results.

Validates chunks produced by any chunking strategy.  Checks:

1. **Empty chunks** — chunks with no text content.
2. **Duplicate content** — exact text duplicates (by hash).
3. **Oversized chunks** — exceeding ``max_chunk_size``.
4. **Tiny chunks** — below ``min_chunk_size`` (skip last chunk).
5. **Missing page numbers** — warn when page estimation failed.
6. **Invalid offsets** — negative or overlapping ranges.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

from src.ai_core.chunking.models import Chunk, ChunkingResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Outcome of a validation pass.

    Attributes:
        valid: ``True`` when no errors and only acceptable warnings.
        errors: Fatal issues that should reject the result.
        warnings: Non-fatal observations.
        chunk_errors: Per-chunk index to error message mapping.
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    chunk_errors: dict[int, str] = field(default_factory=dict)

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Combine two validation results."""
        return ValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            chunk_errors={**self.chunk_errors, **other.chunk_errors},
        )


class ValidationEngine:
    """Validates chunks and chunking results.

    Configured with thresholds from ``ChunkingConfiguration`` or direct
    keyword arguments.
    """

    def __init__(
        self,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
        strict: bool = False,
        additional_checks: list[str] | None = None,
    ) -> None:
        """Initialize the validation engine.

        Args:
            min_chunk_size: Minimum allowed chunk length (characters).
            max_chunk_size: Maximum allowed chunk length (characters).
            strict: When ``True``, warnings become errors.
            additional_checks: Optional list of check names to enable
                               (all enabled by default).
        """
        self._min_chunk_size = min_chunk_size
        self._max_chunk_size = max_chunk_size
        self._strict = strict

        # All available checks
        self._checks: dict[str, Any] = {
            "empty": self._check_empty,
            "duplicate": self._check_duplicates,
            "oversized": self._check_oversized,
            "tiny": self._check_tiny,
            "page_number": self._check_page_numbers,
            "offsets": self._check_offsets,
        }

        if additional_checks is not None:
            self._checks = {k: v for k, v in self._checks.items() if k in additional_checks}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, result: ChunkingResult) -> ValidationResult:
        """Run all checks on *result*.

        Args:
            result: The output of a chunking run.

        Returns:
            A ``ValidationResult`` with errors and warnings.
        """
        overall = ValidationResult()
        for name, check in self._checks.items():
            try:
                vr = check(result)
                overall = overall.merge(vr)
            except Exception:
                logger.exception("Validation check '%s' failed", name)
                overall.errors.append(f"Validation check '{name}' raised an exception")
                overall.valid = False

        # In strict mode, promote warnings to errors
        if self._strict and overall.warnings:
            overall.errors.extend(overall.warnings)
            overall.warnings = []
            overall.valid = False

        return overall

    def validate_chunk(self, chunk: Chunk) -> ValidationResult:
        """Run checks on a single chunk.

        Useful for streaming or incremental validation.
        """
        return self._check_empty_for_chunk(chunk)

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_empty(self, result: ChunkingResult) -> ValidationResult:
        """Check for chunks with empty text."""
        vr = ValidationResult()
        for i, chunk in enumerate(result.chunks):
            if not chunk.text or not chunk.text.strip():
                msg = f"Chunk {i} has empty text"
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
                vr.valid = False
        return vr

    def _check_empty_for_chunk(self, chunk: Chunk) -> ValidationResult:
        vr = ValidationResult()
        if not chunk.text or not chunk.text.strip():
            vr.warnings.append("Chunk has empty text")
            vr.valid = False
        return vr

    def _check_duplicates(self, result: ChunkingResult) -> ValidationResult:
        """Check for exact text duplicates across chunks."""
        vr = ValidationResult()
        seen: dict[str, list[int]] = {}
        for i, chunk in enumerate(result.chunks):
            h = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
            if h in seen:
                msg = f"Chunk {i} is a duplicate of chunk(s) {seen[h]}"
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
            else:
                seen[h] = []
            seen[h].append(i)
        return vr

    def _check_oversized(self, result: ChunkingResult) -> ValidationResult:
        """Check for chunks exceeding ``max_chunk_size``."""
        vr = ValidationResult()
        for i, chunk in enumerate(result.chunks):
            if len(chunk.text) > self._max_chunk_size:
                msg = (
                    f"Chunk {i} exceeds max_chunk_size "
                    f"({len(chunk.text)} > {self._max_chunk_size})"
                )
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
        return vr

    def _check_tiny(self, result: ChunkingResult) -> ValidationResult:
        """Check for chunks below ``min_chunk_size``.

        The last chunk is exempt (it's often a partial remainder).
        """
        vr = ValidationResult()
        n = len(result.chunks)
        for i, chunk in enumerate(result.chunks):
            if i == n - 1:
                continue  # last chunk is allowed to be short
            if len(chunk.text) < self._min_chunk_size:
                msg = (
                    f"Chunk {i} is below min_chunk_size "
                    f"({len(chunk.text)} < {self._min_chunk_size})"
                )
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
        return vr

    def _check_page_numbers(self, result: ChunkingResult) -> ValidationResult:
        """Warn when page number is missing."""
        vr = ValidationResult()
        for i, chunk in enumerate(result.chunks):
            if chunk.page_number is None:
                vr.warnings.append(f"Chunk {i} has no page number")
        return vr

    def _check_offsets(self, result: ChunkingResult) -> ValidationResult:
        """Check for invalid or overlapping offsets."""
        vr = ValidationResult()
        for i, chunk in enumerate(result.chunks):
            if chunk.start_offset < 0 or chunk.end_offset < 0:
                msg = f"Chunk {i} has negative offset"
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
                vr.valid = False
            if chunk.start_offset > chunk.end_offset:
                msg = (
                    f"Chunk {i} has start_offset > end_offset "
                    f"({chunk.start_offset} > {chunk.end_offset})"
                )
                vr.chunk_errors[i] = msg
                vr.warnings.append(msg)
                vr.valid = False

        # Check for overlapping ranges between adjacent chunks
        sorted_chunks = sorted(result.chunks, key=lambda c: c.start_offset)
        for i in range(1, len(sorted_chunks)):
            prev = sorted_chunks[i - 1]
            curr = sorted_chunks[i]
            if curr.start_offset < prev.end_offset:
                vr.warnings.append(
                    f"Overlap between chunk at offset {prev.start_offset} "
                    f"and chunk at offset {curr.start_offset}"
                )
        return vr
