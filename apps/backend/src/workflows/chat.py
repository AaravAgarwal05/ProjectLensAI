"""Chat workflow — retrieve context, build prompt, generate response, format citations."""

import logging
from typing import Any

from src.ai_core.chunking.base import DocumentChunk
from src.ai_core.context.builder import ContextBuilder
from src.ai_core.embedding.base import BaseEmbeddingProvider
from src.ai_core.llm.base import BaseLLMProvider
from src.ai_core.prompting.base import PromptManager
from src.ai_core.retrieval.base import BaseRetriever, RetrievedChunk
from src.workflows.base import BaseWorkflow

logger = logging.getLogger(__name__)


class ChatWorkflow(BaseWorkflow):
    """End-to-end RAG chat workflow.

    Steps:
        1. Validate and parse input.
        2. Retrieve relevant chunks for the query.
        3. Build a consolidated context.
        4. Assemble the LLM prompt.
        5. Generate the response.
        6. Extract and format citations.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        llm: BaseLLMProvider,
        embedder: BaseEmbeddingProvider | None = None,
        prompt_manager: PromptManager | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._embedder = embedder
        self._prompt_manager = prompt_manager or PromptManager()
        self._context_builder = context_builder or ContextBuilder()

        # Register a default chat prompt
        self._prompt_manager.add(
            "chat_default",
            "You are a helpful assistant. Answer the user's question based "
            "on the provided context.\n\nContext:\n{context}\n\n"
            "Question: {query}\n\nAnswer:",
        )

    def validate_input(self, data: dict[str, Any]) -> bool:
        """Ensure required fields are present: ``query`` (str)."""
        return isinstance(data.get("query"), str) and len(data["query"].strip()) > 0

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run the chat workflow.

        Args:
            context: Must contain ``query`` (str); may contain
                     ``conversation_history`` (list), ``top_k`` (int).

        Returns:
            A dict with keys ``reply``, ``citations``, ``chunks``.
        """
        query: str = context["query"]
        top_k: int = context.get("top_k", 5)

        # Step 2: Retrieve
        retrieved: list[RetrievedChunk] = await self._retriever.retrieve(query, top_k=top_k)
        chunks = [
            DocumentChunk(content=r.content, metadata=r.metadata)
            for r in retrieved
        ]

        # Step 3: Build context
        ctx = self._context_builder.build(query, chunks)

        # Step 4: Build prompt
        prompt = self._prompt_manager.get("chat_default").format(
            context=ctx,
            query=query,
        )

        # Step 5: Generate
        reply = await self._llm.generate(prompt)

        # Step 6: Format citations
        citations = [
            {
                "text": r.content[:200],
                "score": round(r.score, 4),
                "document_id": r.document_id,
            }
            for r in retrieved[:5]
        ]

        return {
            "reply": reply,
            "citations": citations,
            "chunks": len(chunks),
        }
