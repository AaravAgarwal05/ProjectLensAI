"""Tests for LLM data models."""

from src.ai_core.llm.models import (
    GenerationMetadata,
    GenerationStatistics,
    LLMRequest,
    LLMResponse,
    ProviderHealth,
    StreamingChunk,
    TokenUsage,
)


class TestTokenUsage:
    def test_defaults(self):
        t = TokenUsage()
        assert t.prompt_tokens == 0
        assert t.completion_tokens == 0
        assert t.total_tokens == 0

    def test_values(self):
        t = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert t.total_tokens == 30


class TestGenerationMetadata:
    def test_defaults(self):
        m = GenerationMetadata()
        assert m.model == ""
        assert m.latency_ms == 0.0

    def test_with_usage(self):
        usage = TokenUsage(prompt_tokens=5, completion_tokens=15)
        m = GenerationMetadata(model="test", token_usage=usage)
        assert m.token_usage.completion_tokens == 15


class TestLLMRequest:
    def test_defaults(self):
        req = LLMRequest()
        assert req.temperature == 0.7
        assert req.max_tokens == 2048
        assert req.stream is False
        assert req.metadata == {}

    def test_custom(self):
        req = LLMRequest(
            system_prompt="You are a bot.",
            user_prompt="Hello",
            temperature=0.5,
            model_name="test-model",
            stream=True,
        )
        assert req.system_prompt == "You are a bot."
        assert req.temperature == 0.5
        assert req.stream is True


class TestLLMResponse:
    def test_defaults(self):
        resp = LLMResponse()
        assert resp.text == ""
        assert resp.successful is True
        assert resp.citations == []

    def test_with_text(self):
        resp = LLMResponse(text="Hello world", successful=True)
        assert resp.text == "Hello world"

    def test_failed_response(self):
        resp = LLMResponse(text="", successful=False)
        assert resp.successful is False


class TestStreamingChunk:
    def test_defaults(self):
        c = StreamingChunk()
        assert c.text == ""
        assert c.finish_reason is None
        assert c.token_count == 0

    def test_finish(self):
        c = StreamingChunk(text="", finish_reason="stop", token_count=42)
        assert c.finish_reason == "stop"
        assert c.token_count == 42


class TestProviderHealth:
    def test_unhealthy_default(self):
        h = ProviderHealth()
        assert h.healthy is False
        assert h.model_available is False

    def test_healthy(self):
        h = ProviderHealth(healthy=True, model_available=True, latency_ms=5.0)
        assert h.healthy is True
        assert h.latency_ms == 5.0

    def test_with_error(self):
        h = ProviderHealth(healthy=False, error="Connection refused")
        assert h.error == "Connection refused"


class TestGenerationStatistics:
    def test_defaults(self):
        s = GenerationStatistics()
        assert s.tokens_per_second == 0.0
        assert s.memory_usage_mb == 0.0

    def test_values(self):
        s = GenerationStatistics(
            prompt_tokens=10,
            completion_tokens=50,
            total_tokens=60,
            tokens_per_second=25.0,
            total_latency_ms=2000.0,
        )
        assert s.tokens_per_second == 25.0
        assert s.total_latency_ms == 2000.0
