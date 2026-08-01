"""LLM configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMConfiguration:
    """Configuration for the LLM engine."""

    provider: str = os.getenv("LLM_PROVIDER", "opencode_zen")
    model_name: str = "deepseek-v4-flash-free"
    embedding_model: str = "nomic-embed-text"
    prompt_version: str = "v2"

    temperature: float = 0.3
    top_p: float = 0.85
    max_tokens: int = 4096
    context_window: int = 16384  # DeepSeek v4 Flash: 16k context
    timeout: float = 30.0
    base_url: str = "https://opencode.ai/zen/v1"

    max_retries: int = 2
    retry_delay: float = 1.0

    enable_streaming: bool = True
    stream_timeout: float = 120.0

    enable_validation: bool = True
    strict_validation: bool = False

    enable_benchmark: bool = False

    system_prompt: str = (
        "You are a document analysis assistant. Answer STRICTLY from the retrieved context.\n"
        "Rules:\n"
        "1. Base every claim on the retrieved context. Never use outside knowledge.\n"
        "2. Use the context to answer: extract the relevant facts, and aggregate or "
        "compare across chunks when the question asks for it (e.g. highest/lowest, "
        "totals, distributions).\n"
        "3. For each fact you state, cite the chunk it came from as [Chunk N].\n"
        "4. Do not add general knowledge, extra examples, or elaborations "
        "not present in the context.\n"
        "5. Only if the context genuinely has none of the information needed, "
        "answer exactly: \"The retrieved context doesn't cover this question.\"\n"
        "6. If only part of the answer is in the context, answer that part "
        "and note the rest is not covered.\n"
        "7. Format your answer in plain Markdown (bold with **text**, "
        "lists, headings). Never output raw HTML tags like <strong>."
    )

    fallback_models: list[str] = field(default_factory=lambda: ["llama3.2:1b"])

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
            "prompt_version": self.prompt_version,
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
