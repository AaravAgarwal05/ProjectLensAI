"""Data models for the LLM engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenUsage:
    """Token counts for a generation request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class GenerationMetadata:
    """Metadata attached to a generation response."""

    model: str = ""
    provider: str = ""
    timestamp: float = 0.0
    latency_ms: float = 0.0
    token_usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass
class LLMRequest:
    """Request payload for LLM generation."""

    system_prompt: str = ""
    user_prompt: str = ""
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    model_name: str = ""
    stream: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Complete response from LLM generation."""

    text: str = ""
    metadata: GenerationMetadata = field(default_factory=GenerationMetadata)
    citations: list[str] = field(default_factory=list)
    successful: bool = True


@dataclass
class StreamingChunk:
    """A single streaming chunk from LLM generation."""

    text: str = ""
    finish_reason: str | None = None
    token_count: int = 0


@dataclass
class ProviderHealth:
    """Health status of an LLM provider."""

    healthy: bool = False
    model_available: bool = False
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class GenerationStatistics:
    """Benchmark statistics for generation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tokens_per_second: float = 0.0
    time_to_first_token_ms: float = 0.0
    total_latency_ms: float = 0.0
    memory_usage_mb: float = 0.0
