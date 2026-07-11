"""Retrieval engine — transform queries into ranked relevant chunks.

Provides:
- **Retrievers**: Dense, Hybrid, MultiQuery
- **Rerankers**: None, CrossEncoder
- **Pipeline**: Query → Retriever → Reranker → Validation → Results
- **Hooks**: before/after retrieval and reranking lifecycle
- **Validation**: Result quality checks
- **Benchmarks**: Latency, recall, precision, MRR, NDCG, throughput
"""

from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.benchmark import RetrievalBenchmark, RetrievalBenchmarkReport
from src.ai_core.retrieval.configuration import RetrieverConfiguration
from src.ai_core.retrieval.exceptions import (
    EmbeddingError,
    EmptyQueryError,
    RerankerNotFoundError,
    RetrievalError,
    RetrieverNotFoundError,
    ScoreThresholdNotMetError,
    SearchError,
)
from src.ai_core.retrieval.factory import RetrieverFactory
from src.ai_core.retrieval.hooks import (
    RetrievalHook,
    RetrievalHookEvent,
    RetrievalHookRegistry,
)
from src.ai_core.retrieval.models import (
    RetrievalMetadata,
    RetrievalResult,
    RetrievalStatistics,
    RetrievedChunk,
    SearchQuery,
)
from src.ai_core.retrieval.pipeline import RetrievalPipeline
from src.ai_core.retrieval.registry import RetrieverRegistry
from src.ai_core.retrieval.reranking.base import Reranker
from src.ai_core.retrieval.reranking.factory import RerankerFactory
from src.ai_core.retrieval.reranking.registry import RerankerRegistry
from src.ai_core.retrieval.validation import RetrievalValidationEngine, RetrievalValidationResult

__all__ = [
    "Retriever",
    "RetrieverConfiguration",
    "RetrieverRegistry",
    "RetrieverFactory",
    "RetrievalPipeline",
    "SearchQuery",
    "RetrievedChunk",
    "RetrievalResult",
    "RetrievalMetadata",
    "RetrievalStatistics",
    "Reranker",
    "RerankerRegistry",
    "RerankerFactory",
    "RetrievalHook",
    "RetrievalHookEvent",
    "RetrievalHookRegistry",
    "RetrievalValidationEngine",
    "RetrievalValidationResult",
    "RetrievalBenchmark",
    "RetrievalBenchmarkReport",
    "RetrievalError",
    "RetrieverNotFoundError",
    "RerankerNotFoundError",
    "EmbeddingError",
    "SearchError",
    "EmptyQueryError",
    "ScoreThresholdNotMetError",
]
