"""RAG-powered chat service for document Q&A.

Retrieves relevant chunks from ChromaDB, builds a context-rich prompt,
and generates answers via the Ollama LLM.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Any

from src.ai_core.embedding.providers.ollama import OllamaEmbeddingProvider
from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.models import LLMRequest
from src.ai_core.llm.providers.ollama import OllamaProvider
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_DEFAULT_SYSTEM_PROMPT = (
    "You are a precise document analysis assistant. "
    "Answer the user's question using ONLY the provided document excerpts. "
    "If the excerpts don't contain enough information to answer, say so clearly. "
    "When you use specific information reference it by its excerpt number [1], [2], etc. "
    "Be concise and accurate."
)


class RAGChatService:
    """Answers user questions about a report using retrieval-augmented generation.

    Pipeline::

        query -> embed -> ChromaDB similarity search -> prompt -> Ollama LLM -> response
    """

    def __init__(
        self,
        chroma_host: str | None = None,
        chroma_port: int | None = None,
        top_k: int = 5,
    ) -> None:
        _settings = get_settings()
        self._chroma_host = chroma_host or _settings.CHROMA_HOST
        self._chroma_port = chroma_port or _settings.CHROMA_PORT
        self._top_k = top_k
        self._embedding_provider = OllamaEmbeddingProvider(
            model_name="nomic-embed-text",
            base_url=_settings.ollama_base_url,
        )
        self._llm_provider = OllamaProvider(
            config=LLMConfiguration(base_url=_settings.ollama_base_url)
        )
        self._llm_config = LLMConfiguration(base_url=_settings.ollama_base_url)
        self._chroma_client: Any | None = None

    # ------------------------------------------------------------------
    # Request tracing
    # ------------------------------------------------------------------

    @staticmethod
    def _make_trace_id() -> str:
        """Generate a short request trace ID for log correlation."""
        import uuid
        return uuid.uuid4().hex[:12]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def answer(
        self,
        message: str,
        report_ids: list[str],
        trace_id: str | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Generate an answer using RAG over the given report IDs.

        Parameters
        ----------
        message : str
            The user's question.
        report_ids : list[str]
            Document report IDs to search.
        trace_id : str or None
            Optional request trace ID for log correlation.

        Returns
        -------
            (answer_text, citations_list)
            citations_list contains dicts with keys ``report_id``, ``chunk_id``,
            ``score``, ``report_title``, ``page_number``, ``section_name``.
        """
        tid = trace_id or self._make_trace_id()
        logger.info("[%s] RAG answer: %d reports, query=%s", tid, len(report_ids), message[:80])

        chunks = await self._retrieve_chunks(message, report_ids, trace_id=tid)

        if not chunks:
            logger.info("[%s] No relevant chunks found", tid)
            return (
                "I couldn't find any relevant content in the document "
                "to answer your question. Make sure the document has been "
                "fully processed and try rephrasing your question.",
                [],
            )

        context = self._format_context(chunks)
        system_prompt = _DEFAULT_SYSTEM_PROMPT
        user_prompt = (
            f"Document excerpts:\n\n{context}\n\n"
            f"---\n\n"
            f"Question: {message}\n\n"
            f"Answer based on the excerpts above:"
        )

        request = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self._llm_config.temperature,
            max_tokens=self._llm_config.max_tokens,
        )

        response = await self._llm_provider.generate(request)

        citations = [
            {
                "report_id": c["report_id"],
                "report_title": "",
                "page_number": None,
                "section_name": "",
                "chunk_id": c["chunk_id"],
                "score": c["score"],
            }
            for c in chunks[: self._top_k]
        ]

        logger.info("[%s] RAG answer: %d chunks, %d tokens", tid, len(chunks), len(response.text))
        return response.text, citations

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _embed_with_cache(self, text: str, trace_id: str = "") -> list[float]:
        """Embed *text*, using Redis as a vector cache for Ollama embeddings.

        Falls back to uncached embedding when Redis is unavailable.
        Cache key uses SHA-256 to avoid Python's per-process salted hash().
        """
        # Only cache for Ollama embedding provider
        if self._embedding_provider.provider_name != "ollama":
            return await self._embedding_provider.embed(text)

        cache_key = "embedding:" + hashlib.sha256(text.encode()).hexdigest()
        try:
            from src.infra.redis import get_redis

            redis_client = await get_redis()
            cached = await redis_client.get(cache_key)
            if cached is not None:
                parsed = json.loads(cached)
                if isinstance(parsed, list) and all(isinstance(v, float) for v in parsed):
                    logger.debug("[%s] Embedding cache HIT key=%s", trace_id, cache_key[:16])
                    return parsed
                logger.debug("[%s] Embedding cache miss (invalid format) key=%s", trace_id, cache_key[:16])
        except Exception:
            logger.warning("[%s] Redis cache unavailable for embeddings, falling through", trace_id, exc_info=True)

        # Cache miss or Redis unavailable — embed fresh
        vector = await self._embedding_provider.embed(text)

        # Store in Redis with 1-hour TTL
        try:
            from src.infra.redis import set_json

            await set_json(cache_key, vector, expire=3600)
            logger.debug("[%s] Embedding cache SET key=%s", trace_id, cache_key[:16])
        except Exception:
            logger.warning("[%s] Failed to cache embedding in Redis", trace_id, exc_info=True)

        return vector

    async def _retrieve_chunks(
        self,
        message: str,
        report_ids: list[str],
        trace_id: str = "",
    ) -> list[dict[str, Any]]:
        """Retrieve relevant chunks from ChromaDB for each report."""
        all_chunks: list[dict[str, Any]] = []

        # Embed once, reuse across all report collections
        query_vec = await self._embed_with_cache(message, trace_id=trace_id)

        for rid in report_ids:
            collection = await self._get_collection(rid)
            if collection is None:
                logger.info("[%s] No ChromaDB collection for report %s, skipping", trace_id, rid)
                continue

            # Run synchronous ChromaDB query in thread pool to avoid blocking event loop
            results = await asyncio.to_thread(
                collection.query,
                query_embeddings=[query_vec],
                n_results=self._top_k,
                include=["metadatas", "distances", "documents"],
            )

            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            for i in range(len(ids)):
                all_chunks.append(
                    {
                        "chunk_id": ids[i],
                        "content": documents[i] if documents and i < len(documents) else "",
                        "score": 1.0 / (1.0 + distances[i]) if distances and i < len(distances) else 0.0,
                        "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                        "report_id": rid,
                    }
                )

        all_chunks.sort(key=lambda c: c["score"], reverse=True)
        logger.debug("[%s] Retrieved %d chunks across %d reports", trace_id, len(all_chunks), len(report_ids))
        return all_chunks

    def _format_context(self, chunks: list[dict[str, Any]]) -> str:
        """Format retrieved chunks into a prompt-ready context string."""
        parts: list[str] = []
        for i, c in enumerate(chunks[: self._top_k]):
            parts.append(f"[{i + 1}] (relevance: {c['score']:.2f})\n{c['content']}")
        return "\n\n---\n\n".join(parts)

    async def _get_collection(self, report_id: str) -> Any | None:
        """Get the ChromaDB collection for *report_id*, or None."""
        client = await self._get_chroma_client()
        try:
            return await asyncio.to_thread(client.get_collection, name=f"report_{report_id}")
        except ValueError as exc:
            err = str(exc).lower()
            if "does not exist" in err or "not found" in err:
                logger.debug("Collection report_%s does not exist yet", report_id)
            else:
                logger.warning("ChromaDB error getting report_%s: %s", report_id, exc)
            return None
        except Exception as exc:
            logger.error("Unexpected ChromaDB error for report_%s: %s", report_id, exc)
            return None

    async def _get_chroma_client(self) -> Any:
        """Lazy-init a ChromaDB HTTP client (runs sync init in thread pool)."""
        if self._chroma_client is None:
            import chromadb

            self._chroma_client = await asyncio.to_thread(
                chromadb.HttpClient,
                host=self._chroma_host,
                port=self._chroma_port,
            )
        return self._chroma_client
