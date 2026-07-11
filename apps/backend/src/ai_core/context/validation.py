"""Validation engine for assembled LLMContext."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.ai_core.context.models import LLMContext

logger = logging.getLogger(__name__)


@dataclass
class ContextValidationResult:
    """Result of a validation pass."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ContextValidationEngine:
    """Validates assembled context for quality and completeness."""

    def __init__(self, strict: bool = False) -> None:
        self._strict = strict

    def validate(self, ctx: LLMContext) -> ContextValidationResult:
        """Run all validation checks."""
        vr = ContextValidationResult(valid=True)

        if not ctx.query and self._strict:
            vr.errors.append("Empty query in context")
            vr.valid = False

        if not ctx.chunks and not ctx.conversation_history:
            vr.warnings.append("Empty context — no chunks or history")
            if self._strict:
                vr.valid = False

        self._check_token_limits(ctx, vr)
        self._check_duplicate_chunks(ctx, vr)
        self._check_missing_metadata(ctx, vr)
        self._check_broken_citations(ctx, vr)

        return vr

    def _check_token_limits(self, ctx: LLMContext, vr: ContextValidationResult) -> None:
        if ctx.budget.total <= 0:
            vr.errors.append("Token budget total is zero or negative")
            vr.valid = False
        if ctx.budget.allocated > ctx.budget.total:
            vr.warnings.append(
                f"Token budget exceeded: allocated {ctx.budget.allocated} > "
                f"total {ctx.budget.total}"
            )

    def _check_duplicate_chunks(self, ctx: LLMContext, vr: ContextValidationResult) -> None:
        seen: set[str] = set()
        for c in ctx.chunks:
            key = c.chunk_id
            if key in seen:
                vr.warnings.append(f"Duplicate chunk in context: {key}")
            seen.add(key)

    def _check_missing_metadata(self, ctx: LLMContext, vr: ContextValidationResult) -> None:
        for c in ctx.chunks:
            if not c.source_id:
                vr.warnings.append(f"Chunk '{c.chunk_id}' missing source_id")
            if not c.content:
                vr.errors.append(f"Chunk '{c.chunk_id}' has empty content")
                vr.valid = False

    def _check_broken_citations(self, ctx: LLMContext, vr: ContextValidationResult) -> None:
        chunk_ids = {c.chunk_id for c in ctx.chunks}
        for c in ctx.chunks:
            for citation in c.citations:
                if (
                    citation.startswith("parent:")
                    and citation.removeprefix("parent:") not in chunk_ids
                ):
                    vr.warnings.append(
                        f"Broken parent citation '{citation}' in chunk '{c.chunk_id}'"
                    )
