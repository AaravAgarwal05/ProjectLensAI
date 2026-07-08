"""Chunking engine — document chunking framework with multiple strategies.

Provides:
- **Strategies**: Fixed, Recursive, Heading-Aware (default)
- **Pipelines**: Orchestrated chunking with hooks and validation
- **Validation**: Post-chunking quality checks
- **Benchmarks**: Performance measurement and comparison
"""

from src.ai_core.chunking.base import ChunkingStrategy
from src.ai_core.chunking.benchmark import BenchmarkFramework, BenchmarkReport
from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.exceptions import (
    ChunkerNotFoundError,
    ChunkingError,
    ChunkingValidationError,
    DocumentEmptyError,
)
from src.ai_core.chunking.factory import ChunkingFactory
from src.ai_core.chunking.hooks import ChunkingHook, HookEvent, HookRegistry
from src.ai_core.chunking.models import Chunk, ChunkMetadata, ChunkStatistics, ChunkingResult
from src.ai_core.chunking.pipeline import ChunkingPipeline
from src.ai_core.chunking.registry import ChunkingRegistry
from src.ai_core.chunking.validation import ValidationEngine, ValidationResult

__all__ = [
    # Base
    "ChunkingStrategy",
    # Models
    "Chunk",
    "ChunkMetadata",
    "ChunkStatistics",
    "ChunkingResult",
    # Configuration
    "ChunkingConfiguration",
    # Registry & Factory
    "ChunkingRegistry",
    "ChunkingFactory",
    # Hooks & Pipeline
    "ChunkingHook",
    "HookEvent",
    "HookRegistry",
    "ChunkingPipeline",
    # Validation
    "ValidationEngine",
    "ValidationResult",
    # Benchmark
    "BenchmarkFramework",
    "BenchmarkReport",
    # Exceptions
    "ChunkingError",
    "ChunkerNotFoundError",
    "ChunkingValidationError",
    "DocumentEmptyError",
]
