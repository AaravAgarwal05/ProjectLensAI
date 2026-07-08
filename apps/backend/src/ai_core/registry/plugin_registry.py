"""Central registry for AI plugins — chunkers, embedders, retrievers, LLMs."""

import logging
from typing import Any

from src.ai_core.chunking.base import BaseChunker
from src.ai_core.embedding.base import BaseEmbeddingProvider
from src.ai_core.llm.base import BaseLLMProvider
from src.ai_core.retrieval.base import BaseRetriever

logger = logging.getLogger(__name__)


class AIPluginRegistry:
    """Registry that holds and resolves AI component instances by name.

    Components are registered once at startup and can be retrieved
    throughout the application without re-initialisation.
    """

    def __init__(self) -> None:
        self._chunkers: dict[str, BaseChunker] = {}
        self._embedders: dict[str, BaseEmbeddingProvider] = {}
        self._retrievers: dict[str, BaseRetriever] = {}
        self._llms: dict[str, BaseLLMProvider] = {}

    # ---- chunkers ----

    def register_chunker(self, name: str, chunker: BaseChunker) -> None:
        self._chunkers[name] = chunker
        logger.debug("Registered chunker '%s'", name)

    def get_chunker(self, name: str) -> BaseChunker:
        if name not in self._chunkers:
            msg = f"Unknown chunker: '{name}'"
            raise KeyError(msg)
        return self._chunkers[name]

    # ---- embedders ----

    def register_embedder(self, name: str, embedder: BaseEmbeddingProvider) -> None:
        self._embedders[name] = embedder
        logger.debug("Registered embedder '%s'", name)

    def get_embedder(self, name: str) -> BaseEmbeddingProvider:
        if name not in self._embedders:
            msg = f"Unknown embedder: '{name}'"
            raise KeyError(msg)
        return self._embedders[name]

    # ---- retrievers ----

    def register_retriever(self, name: str, retriever: BaseRetriever) -> None:
        self._retrievers[name] = retriever
        logger.debug("Registered retriever '%s'", name)

    def get_retriever(self, name: str) -> BaseRetriever:
        if name not in self._retrievers:
            msg = f"Unknown retriever: '{name}'"
            raise KeyError(msg)
        return self._retrievers[name]

    # ---- LLMs ----

    def register_llm(self, name: str, llm: BaseLLMProvider) -> None:
        self._llms[name] = llm
        logger.debug("Registered LLM '%s'", name)

    def get_llm(self, name: str) -> BaseLLMProvider:
        if name not in self._llms:
            msg = f"Unknown LLM: '{name}'"
            raise KeyError(msg)
        return self._llms[name]

    # ---- introspection ----

    @property
    def available_chunkers(self) -> list[str]:
        return list(self._chunkers)

    @property
    def available_embedders(self) -> list[str]:
        return list(self._embedders)

    @property
    def available_retrievers(self) -> list[str]:
        return list(self._retrievers)

    @property
    def available_llms(self) -> list[str]:
        return list(self._llms)
