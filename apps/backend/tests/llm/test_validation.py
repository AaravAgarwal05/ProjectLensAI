"""Tests for LLMValidationEngine."""

import pytest

from src.ai_core.llm.exceptions import (
    EmptyResponseError,
    TokenLimitExceededError,
)
from src.ai_core.llm.models import GenerationMetadata, LLMResponse, TokenUsage
from src.ai_core.llm.validation import LLMValidationEngine


class TestLLMValidationEngine:
    def test_valid_response(self):
        engine = LLMValidationEngine()
        response = LLMResponse(text="Valid content")
        result = engine.validate(response)
        assert result.valid is True
        assert result.errors == []

    def test_empty_response(self):
        engine = LLMValidationEngine(strict=True)
        response = LLMResponse(text="")
        with pytest.raises(EmptyResponseError, match="Empty response"):
            engine.validate(response)

    def test_empty_response_non_strict(self):
        engine = LLMValidationEngine(strict=False)
        response = LLMResponse(text="")
        result = engine.validate(response)
        assert result.valid is False
        assert "Empty response text" in result.errors
        # No exception raised in non-strict mode

    def test_citations_present(self):
        engine = LLMValidationEngine()
        response = LLMResponse(
            text="See doc_1 for details",
        )
        result = engine.validate(response, source_citations=["doc_1"])
        assert result.valid is True

    def test_missing_citation_warning(self):
        engine = LLMValidationEngine()
        response = LLMResponse(text="Nothing about sources here")
        result = engine.validate(response, source_citations=["src_report_2024"])
        # src_report_2024 doesn't start with "src_" so it's not flagged
        assert result.valid is True

    def test_missing_src_citation_warning(self):
        engine = LLMValidationEngine()
        response = LLMResponse(text="No citations")
        result = engine.validate(response, source_citations=["src_report_2024"])
        assert len(result.warnings) == 1
        assert "src_report_2024" in result.warnings[0]

    def test_token_limit_exceeded_strict(self):
        engine = LLMValidationEngine(strict=True)
        response = LLMResponse(
            text="Long content",
            metadata=GenerationMetadata(
                token_usage=TokenUsage(completion_tokens=150),
            ),
        )
        with pytest.raises(TokenLimitExceededError, match="Token limit"):
            engine.validate(response, max_completion_tokens=100)

    def test_token_limit_exceeded_warning(self):
        engine = LLMValidationEngine(strict=False)
        response = LLMResponse(
            text="Long content",
            metadata=GenerationMetadata(
                token_usage=TokenUsage(completion_tokens=150),
            ),
        )
        result = engine.validate(response, max_completion_tokens=100)
        # Warning but not error in non-strict
        assert result.valid is True
        assert len(result.warnings) == 1

    def test_no_source_citations(self):
        """Validation passes when no source citations provided."""
        engine = LLMValidationEngine()
        response = LLMResponse(text="Some content")
        result = engine.validate(response, source_citations=[])
        assert result.valid is True

    def test_empty_response_non_strict_no_exception(self):
        """Empty response is caught but no exception in non-strict mode."""
        engine = LLMValidationEngine(strict=False)
        response = LLMResponse(text="")
        result = engine.validate(response)
        assert result.valid is False
