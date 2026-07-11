"""Tests for OllamaProvider."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.ai_core.llm.exceptions import (
    GenerationError,
    ProviderNotAvailableError,
    StreamingError,
    TimeoutError,
)
from src.ai_core.llm.models import LLMRequest, LLMResponse
from src.ai_core.llm.providers.ollama import OllamaProvider
from tests.llm.fixtures import (
    make_config,
    make_successful_generate_response,
    make_tags_response,
)


def _mock_ctx(resp: httpx.Response) -> MagicMock:
    """Wrap a Response into an async-context-manager mock for client.stream."""
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


def _make_provider() -> OllamaProvider:
    """Create an OllamaProvider with mocked HTTP client."""
    config = make_config()
    prov = OllamaProvider(config)
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.is_closed = False
    prov._client = mock_client
    return prov


def _sample_request(**kwargs: object) -> LLMRequest:
    defaults = {
        "system_prompt": "You are a test assistant.",
        "user_prompt": "Hello, test!",
        "temperature": 0.5,
        "max_tokens": 100,
    }
    defaults.update(kwargs)
    return LLMRequest(**defaults)


class TestOllamaProviderNonStreaming:
    """Non-streaming generation tests."""

    async def test_generate_success(self):
        prov = _make_provider()
        req = _sample_request()
        response = make_successful_generate_response(
            text="Hello from Ollama",
            prompt_eval_count=15,
            eval_count=8,
        )
        prov._client.post = AsyncMock(return_value=response)  # type: ignore[method-assign]

        result = await prov.generate(req)
        assert isinstance(result, LLMResponse)
        assert result.text == "Hello from Ollama"
        assert result.successful is True
        assert result.metadata.token_usage.prompt_tokens == 15
        assert result.metadata.token_usage.completion_tokens == 8

    async def test_generate_http_error(self):
        prov = _make_provider()
        req = _sample_request()
        prov._client.post = AsyncMock(  # type: ignore[method-assign]
            return_value=httpx.Response(status_code=500, text="Internal error")
        )
        with pytest.raises(GenerationError, match="returned status 500"):
            await prov.generate(req)

    async def test_generate_connection_error(self):
        prov = _make_provider()
        req = _sample_request()
        prov._client.post = AsyncMock(  # type: ignore[method-assign]
            side_effect=httpx.ConnectError("Connection refused")
        )
        with pytest.raises(ProviderNotAvailableError, match="connection failed"):
            await prov.generate(req)

    async def test_generate_timeout(self):
        prov = _make_provider()
        req = _sample_request()
        prov._client.post = AsyncMock(  # type: ignore[method-assign]
            side_effect=httpx.TimeoutException("Timed out")
        )
        with pytest.raises(TimeoutError, match="timed out"):
            await prov.generate(req)

    async def test_generate_empty_response(self):
        prov = _make_provider()
        req = _sample_request()
        response = make_successful_generate_response(text="")
        prov._client.post = AsyncMock(return_value=response)  # type: ignore[method-assign]
        result = await prov.generate(req)
        assert result.text == ""
        assert result.successful is True

    async def test_generate_custom_model(self):
        prov = _make_provider()
        req = _sample_request(model_name="custom:latest")
        response = make_successful_generate_response(text="ok")
        prov._client.post = AsyncMock(return_value=response)  # type: ignore[method-assign]
        result = await prov.generate(req)
        assert result.metadata.model == "custom:latest"


class TestOllamaProviderStreaming:
    """Streaming generation tests."""

    async def test_generate_stream_success(self):
        prov = _make_provider()
        req = _sample_request()
        stream_lines = [
            b'{"response": "Hello", "done": false}\n',
            b'{"response": " world", "done": false}\n',
            b'{"response": "", "done": true, "eval_count": 3}\n',
        ]

        async def _aiter_lines():
            for line in stream_lines:
                yield line

        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.aiter_lines = _aiter_lines
        prov._client.stream = MagicMock(return_value=_mock_ctx(resp))

        chunks = []
        async for chunk in prov.generate_stream(req):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].text == "Hello"
        assert chunks[1].text == " world"
        assert chunks[2].finish_reason == "stop"

    async def test_generate_stream_http_error(self):
        prov = _make_provider()
        req = _sample_request()

        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 500
        prov._client.stream = MagicMock(return_value=_mock_ctx(resp))

        with pytest.raises(StreamingError, match="returned status 500"):
            async for _ in prov.generate_stream(req):
                pass

    async def test_generate_stream_timeout(self):
        prov = _make_provider()
        req = _sample_request()
        prov._client.stream = MagicMock(side_effect=httpx.TimeoutException("Stream timed out"))
        with pytest.raises(TimeoutError, match="timed out"):
            async for _ in prov.generate_stream(req):
                pass

    async def test_generate_stream_invalid_json(self):
        prov = _make_provider()
        req = _sample_request()
        stream_lines = [
            b"not json\n",
            b'{"response": "val", "done": false}\n',
            b'{"response": "id", "done": false}\n',
            b'{"response": "", "done": true, "eval_count": 2}\n',
        ]

        async def _aiter_lines():
            for line in stream_lines:
                yield line

        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.aiter_lines = _aiter_lines
        prov._client.stream = MagicMock(return_value=_mock_ctx(resp))

        chunks = []
        async for chunk in prov.generate_stream(req):
            chunks.append(chunk)

        # Invalid line skipped, valid lines processed
        assert len(chunks) == 3
        assert chunks[0].text == "val"
        assert chunks[1].text == "id"
        assert chunks[2].finish_reason == "stop"


class TestOllamaProviderHealth:
    """Health check tests."""

    async def test_healthy(self):
        prov = _make_provider()
        prov._client.get = AsyncMock(  # type: ignore[method-assign]
            return_value=make_tags_response(["test-model:latest"])
        )
        health = await prov.check_health()
        assert health.healthy is True
        assert health.model_available is True

    async def test_unhealthy_connection(self):
        prov = _make_provider()
        prov._client.get = AsyncMock(  # type: ignore[method-assign]
            side_effect=httpx.ConnectError("Connection refused")
        )
        health = await prov.check_health()
        assert health.healthy is False
        assert health.error is not None

    async def test_healthy_model_unavailable(self):
        prov = _make_provider()
        prov._client.get = AsyncMock(  # type: ignore[method-assign]
            return_value=make_tags_response(["other-model:latest"])
        )
        health = await prov.check_health()
        assert health.healthy is True
        assert health.model_available is False

    async def test_is_model_available(self):
        prov = _make_provider()
        prov._client.get = AsyncMock(  # type: ignore[method-assign]
            return_value=make_tags_response(["test-model:latest"])
        )
        available = await prov.is_model_available("test-model:latest")
        assert available is True

    async def test_is_model_not_available(self):
        prov = _make_provider()
        prov._client.get = AsyncMock(  # type: ignore[method-assign]
            return_value=make_tags_response(["other:latest"])
        )
        available = await prov.is_model_available("test-model:latest")
        assert available is False


class TestOllamaProviderTokenCount:
    """Token count estimation tests."""

    async def test_count_tokens_empty(self):
        prov = _make_provider()
        count = await prov.count_tokens("")
        assert count == 0

    async def test_count_tokens_estimate(self):
        prov = _make_provider()
        count = await prov.count_tokens("hello world")
        # 11 chars // 4 = 2, max(1, 2) = 2
        assert count == 2


class TestOllamaProviderConfig:
    """Configuration tests."""

    def test_provider_name(self):
        prov = _make_provider()
        assert prov.provider_name == "ollama"

    def test_default_model(self):
        prov = OllamaProvider()
        assert prov._config.model_name == "qwen3.5:4b"

    def test_custom_config(self):
        config = make_config(model_name="custom:latest")
        prov = OllamaProvider(config)
        assert prov._config.model_name == "custom:latest"

    def test_configure(self):
        prov = _make_provider()
        prov.configure({"temperature": 0.1, "max_tokens": 512})
        assert prov._config.temperature == 0.1
        assert prov._config.max_tokens == 512
