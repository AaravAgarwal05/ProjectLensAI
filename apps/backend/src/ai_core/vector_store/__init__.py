"""Vector store and indexing engine — persist embedded chunks.

Provides:
- **Providers**: ChromaDB, pgvector
- **Indexing Engine**: Batch index, delete, reindex, retry
- **Validation**: Vector quality and metadata checks
- **Benchmarks**: Insert/delete/update throughput, memory, latency
"""

from src.ai_core.vector_store.base import VectorStore
from src.ai_core.vector_store.benchmark import VectorStoreBenchmark, VectorStoreBenchmarkReport
from src.ai_core.vector_store.configuration import VectorStoreConfiguration
from src.ai_core.vector_store.exceptions import (
    CollectionNotFoundError,
    DimensionMismatchError,
    DocumentNotFoundError,
    StoreConnectionError,
    StoreNotFoundError,
    VectorStoreError,
)
from src.ai_core.vector_store.factory import VectorStoreFactory
from src.ai_core.vector_store.indexing import IndexingEngine
from src.ai_core.vector_store.models import (
    DeleteResult,
    IndexingResult,
    IndexingStatistics,
    UpdateResult,
    VectorDocument,
    VectorMetadata,
)
from src.ai_core.vector_store.registry import VectorStoreRegistry
from src.ai_core.vector_store.validation import (
    IndexValidationResult,
    VectorStoreValidationEngine,
)

__all__ = [
    "VectorStore",
    "VectorStoreConfiguration",
    "VectorStoreRegistry",
    "VectorStoreFactory",
    "VectorStoreBenchmark",
    "VectorStoreBenchmarkReport",
    "VectorDocument",
    "VectorMetadata",
    "IndexingResult",
    "IndexingStatistics",
    "DeleteResult",
    "UpdateResult",
    "IndexingEngine",
    "IndexValidationResult",
    "VectorStoreValidationEngine",
    "VectorStoreError",
    "StoreNotFoundError",
    "CollectionNotFoundError",
    "DocumentNotFoundError",
    "DimensionMismatchError",
    "StoreConnectionError",
]
