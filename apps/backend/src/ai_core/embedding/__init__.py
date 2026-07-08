"""Embedding engine — text-to-vector framework with multiple providers.

Provides:
- **Providers**: SentenceTransformers, Ollama
- **Pipeline**: Orchestrated embedding with batching, hooks, validation
- **Validation**: Vector quality checks (NaN, inf, dims, duplicates)
- **Benchmarks**: Latency, throughput, memory measurement
"""

from src.ai_core.embedding.base import EmbeddingProvider
from src.ai_core.embedding.benchmark import EmbeddingBenchmarkFramework, EmbeddingBenchmarkReport
from src.ai_core.embedding.configuration import EmbeddingConfiguration
from src.ai_core.embedding.exceptions import (
    EmbeddingError,
    EmbeddingValidationError,
    ModelNotAvailableError,
    ProviderConnectionError,
    ProviderNotFoundError,
)
from src.ai_core.embedding.factory import EmbeddingFactory
from src.ai_core.embedding.hooks import EmbeddingHook, EmbeddingHookEvent, EmbeddingHookRegistry
from src.ai_core.embedding.models import (
    EmbeddedChunk,
    EmbeddingMetadata,
    EmbeddingResult,
    EmbeddingStatistics,
    EmbeddingVector,
)
from src.ai_core.embedding.pipeline import EmbeddingPipeline
from src.ai_core.embedding.registry import EmbeddingRegistry
from src.ai_core.embedding.validation import EmbeddingValidationEngine, EmbeddingValidationResult

__all__ = [
    "EmbeddingProvider",
    "EmbeddingConfiguration",
    "EmbeddingRegistry",
    "EmbeddingFactory",
    "EmbeddingPipeline",
    "EmbeddingHook",
    "EmbeddingHookEvent",
    "EmbeddingHookRegistry",
    "EmbeddingVector",
    "EmbeddedChunk",
    "EmbeddingMetadata",
    "EmbeddingResult",
    "EmbeddingStatistics",
    "EmbeddingValidationEngine",
    "EmbeddingValidationResult",
    "EmbeddingBenchmarkFramework",
    "EmbeddingBenchmarkReport",
    "EmbeddingError",
    "ProviderNotFoundError",
    "EmbeddingValidationError",
    "ModelNotAvailableError",
    "ProviderConnectionError",
]
