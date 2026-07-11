"""Context manager — transform retrieval results into LLM-ready context.

Provides:
- **Models**: LLMContext, ContextChunk, ConversationMessage, etc.
- **Strategies**: SingleDocument, MultiDocument, Comparison, Summary
- **Pipeline**: Query → Chunks → Budget → LLMContext
- **Hooks**: before/after context and budget lifecycle
- **Validation**: Quality and completeness checks
- **Benchmarks**: Assembly latency, token usage, utilization metrics
"""

from src.ai_core.context.base import ContextStrategy
from src.ai_core.context.benchmark import ContextBenchmark, ContextBenchmarkReport
from src.ai_core.context.budget import TokenBudgetManager
from src.ai_core.context.chunk_selection import ChunkSelectionStrategy
from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.conversation import ConversationManager
from src.ai_core.context.exceptions import (
    BudgetExceededError,
    ConfigurationError,
    ContextError,
    EmptyContextError,
    MissingMetadataError,
    StrategyNotFoundError,
    ValidationError,
)
from src.ai_core.context.factory import ContextFactory
from src.ai_core.context.hooks import (
    ContextHook,
    ContextHookEvent,
    ContextHookRegistry,
)
from src.ai_core.context.metadata import MetadataEnricher
from src.ai_core.context.models import (
    ContextBudget,
    ContextChunk,
    ContextMetadata,
    ContextRole,
    ContextStatistics,
    ContextStrategyType,
    ConversationMessage,
    ConversationSummary,
    LLMContext,
)
from src.ai_core.context.pipeline import ContextAssemblyPipeline
from src.ai_core.context.registry import ContextRegistry
from src.ai_core.context.validation import (
    ContextValidationEngine,
    ContextValidationResult,
)

__all__ = [
    "ContextAssemblyPipeline",
    "ContextBenchmark",
    "ContextBenchmarkReport",
    "ContextBudget",
    "ContextChunk",
    "ContextConfiguration",
    "ContextError",
    "ContextFactory",
    "ContextHook",
    "ContextHookEvent",
    "ContextHookRegistry",
    "ContextMetadata",
    "ContextRegistry",
    "ContextRole",
    "ContextStatistics",
    "ContextStrategy",
    "ContextStrategyType",
    "ContextValidationEngine",
    "ContextValidationResult",
    "ConversationManager",
    "ConversationMessage",
    "ConversationSummary",
    "BudgetExceededError",
    "ChunkSelectionStrategy",
    "ConfigurationError",
    "EmptyContextError",
    "LLMContext",
    "MetadataEnricher",
    "MissingMetadataError",
    "StrategyNotFoundError",
    "TokenBudgetManager",
    "ValidationError",
]
