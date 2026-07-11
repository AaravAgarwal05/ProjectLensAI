"""Validation engine for LLM responses."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.ai_core.llm.exceptions import (
    EmptyResponseError,
    HallucinatedCitationError,
    TokenLimitExceededError,
)
from src.ai_core.llm.models import LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class LLMValidationResult:
    """Result of a validation pass."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class LLMValidationEngine:
    """Validates LLMResponse objects for quality and correctness."""

    def __init__(self, strict: bool = False) -> None:
        self._strict = strict

    def validate(
        self,
        response: LLMResponse,
        source_citations: list[str] | None = None,
        max_completion_tokens: int = 0,
    ) -> LLMValidationResult:
        """Run all validation checks on a response.

        Args:
            response: The response to validate.
            source_citations: Citations that were present in the source context.
            max_completion_tokens: Max allowed completion tokens (0 = no limit).

        Returns:
            A validation result.
        """
        result = LLMValidationResult(valid=True)

        self._check_empty(response, result)
        self._check_citations(response, source_citations or [], result)
        self._check_token_counts(response, max_completion_tokens, result)

        if not result.valid and self._strict:
            msg = "; ".join(result.errors)
            error_map = {
                "empty": EmptyResponseError,
                "citation": HallucinatedCitationError,
                "token": TokenLimitExceededError,
            }
            for keyword, exc_cls in error_map.items():
                if any(keyword in e.lower() for e in result.errors):
                    raise exc_cls(msg)

        return result

    # ------------------------------------------------------------------
    # Internal checks
    # ------------------------------------------------------------------

    def _check_empty(self, response: LLMResponse, result: LLMValidationResult) -> None:
        if not response.text.strip():
            result.errors.append("Empty response text")
            result.valid = False

    def _check_citations(
        self,
        response: LLMResponse,
        source_citations: list[str],
        result: LLMValidationResult,
    ) -> None:
        if not source_citations:
            return
        response_lower = response.text.lower()
        for citation in source_citations:
            if citation.lower() in response_lower:
                continue
            # If citation is a source_id pattern, flag it
            if citation.startswith("src_") or citation.startswith("doc_"):
                result.warnings.append(f"Citation '{citation}' not found verbatim in response")

    def _check_token_counts(
        self,
        response: LLMResponse,
        max_completion_tokens: int,
        result: LLMValidationResult,
    ) -> None:
        if max_completion_tokens <= 0:
            return
        actual = response.metadata.token_usage.completion_tokens
        if actual > max_completion_tokens:
            result.warnings.append(
                f"Completion tokens {actual} exceeded limit {max_completion_tokens}"
            )
            if self._strict:
                result.errors.append(f"Token limit exceeded: {actual} > {max_completion_tokens}")
                result.valid = False
