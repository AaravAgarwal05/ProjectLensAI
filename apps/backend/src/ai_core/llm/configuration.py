"""LLM configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMConfiguration:
    """Configuration for the LLM engine."""

    provider: str = "ollama"
    model_name: str = "llama3.2:1b"
    embedding_model: str = "nomic-embed-text"

    temperature: float = 0.3
    top_p: float = 0.85
    max_tokens: int = 4096
    context_window: int = 262144  # qwen3.5:4b actual capacity
    timeout: float = 120.0
    base_url: str = "http://localhost:11434"

    max_retries: int = 2
    retry_delay: float = 1.0

    enable_streaming: bool = True
    stream_timeout: float = 120.0

    enable_validation: bool = True
    strict_validation: bool = False

    enable_benchmark: bool = False

    system_prompt: str = (
        "You are a document analysis assistant. "
        "Read the retrieved context and answer based only on what you find there. "
        "If the context has no useful information, say the context doesn't cover the question."
    )

    fallback_models: list[str] = field(default_factory=lambda: ["gemma3:1b"])

    def merge(self, params: dict[str, Any]) -> LLMConfiguration:
        """Return a new config with overrides from *params*."""
        d = self.to_dict()
        d.update(params)
        return LLMConfiguration(**d)

    def to_dict(self) -> dict[str, Any]:
        """Return config as a dict."""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "embedding_model": self.embedding_model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "context_window": self.context_window,
            "timeout": self.timeout,
            "base_url": self.base_url,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "enable_streaming": self.enable_streaming,
            "stream_timeout": self.stream_timeout,
            "enable_validation": self.enable_validation,
            "strict_validation": self.strict_validation,
            "enable_benchmark": self.enable_benchmark,
            "system_prompt": self.system_prompt,
            "fallback_models": list(self.fallback_models),
        }

    @staticmethod
    def default() -> LLMConfiguration:
        return LLMConfiguration()
