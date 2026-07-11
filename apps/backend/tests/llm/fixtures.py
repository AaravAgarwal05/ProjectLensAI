"""Shared fixtures and mock helpers for LLM tests.

Import these directly in test modules since we run with --noconftest
to avoid the parent project's conftest (which requires fastapi).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.models import (
    GenerationMetadata,
    LLMRequest,
    LLMResponse,
    TokenUsage,
)
from src.ai_core.llm.providers.ollama import OllamaProvider


def make_config(**overrides: Any) -> LLMConfiguration:
    """Create an LLMConfiguration with test-safe defaults."""
    defaults: dict[str, Any] = {
        "base_url": "http://test-ollama:11434",
        "timeout": 5.0,
        "stream_timeout": 10.0,
        "model_name": "test-model:latest",
    }
    defaults.update(overrides)
    return LLMConfiguration(**defaults)


@pytest.fixture
def mock_ollama_client() -> MagicMock:
    """Create a mock httpx.AsyncClient for Ollama tests."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.is_closed = False
    return client


@pytest.fixture
def provider(mock_ollama_client: MagicMock) -> OllamaProvider:
    """Create an OllamaProvider with mocked HTTP client."""
    config = make_config()
    prov = OllamaProvider(config)
    prov._client = mock_ollama_client
    return prov


def make_successful_generate_response(
    text: str = "Test response",
    prompt_eval_count: int = 10,
    eval_count: int = 20,
) -> httpx.Response:
    """Build a mock successful Ollama generate response."""
    return httpx.Response(
        status_code=200,
        json={
            "model": "test-model:latest",
            "response": text,
            "done": True,
            "prompt_eval_count": prompt_eval_count,
            "eval_count": eval_count,
            "total_duration": 1000000000,
        },
    )


def make_tags_response(
    models: list[str] | None = None,
) -> httpx.Response:
    """Build a mock Ollama /api/tags response."""
    if models is None:
        models = ["test-model:latest"]
    return httpx.Response(
        status_code=200,
        json={"models": [{"name": m, "modified_at": "2024-01-01T00:00:00Z"} for m in models]},
    )


@pytest.fixture
def sample_request() -> LLMRequest:
    return LLMRequest(
        system_prompt="You are a test assistant.",
        user_prompt="Hello, test!",
        temperature=0.5,
        max_tokens=100,
    )


@pytest.fixture
def sample_response() -> LLMResponse:
    return LLMResponse(
        text="This is a test response.",
        metadata=GenerationMetadata(
            model="test-model:latest",
            provider="ollama",
            latency_ms=100.0,
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        ),
        citations=["src_1", "doc_report"],
        successful=True,
    )
