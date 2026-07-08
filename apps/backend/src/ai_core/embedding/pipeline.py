"""Embedding pipeline — orchestrates chunk-to-embedding lifecycle.

Pipeline:
    Chunks → Batching → Embedding Provider → EmbeddedChunks

Hooks:
    before_embedding
    after_embedding
    before_batch
    after_batch
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.ai_core.chunking.models import Chunk
from src.ai_core.embedding.configuration import EmbeddingConfiguration
from src.ai_core.embedding.factory import EmbeddingFactory
from src.ai_core.embedding.hooks import EmbeddingHookRegistry
from src.ai_core.embedding.models import (
    EmbeddedChunk,
    EmbeddingMetadata,
    EmbeddingResult,
    EmbeddingVector,
)
from src.ai_core.embedding.validation import EmbeddingValidationEngine

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Orchestrates the chunk-to-embedding lifecycle with hooks and validation.

    Typical usage::

        pipeline = EmbeddingPipeline(factory)
        result = await pipeline.run(chunks)
    """

    def __init__(
        self,
        factory: EmbeddingFactory | None = None,
        config: EmbeddingConfiguration | None = None,
        hooks: EmbeddingHookRegistry | None = None,
        validation: EmbeddingValidationEngine | None = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            factory: An ``EmbeddingFactory``.  A default factory (with
                      built-in providers) is created if ``None``.
            config: Optional base ``EmbeddingConfiguration``.
            hooks: An optional ``EmbeddingHookRegistry``.
            validation: An optional ``EmbeddingValidationEngine``.
        """
        self._factory = factory or EmbeddingFactory()
        self._base_config = config or EmbeddingConfiguration.default()
        self._hooks = hooks or EmbeddingHookRegistry()
        self._validation = validation

    @property
    def hooks(self) -> EmbeddingHookRegistry:
        return self._hooks

    @property
    def factory(self) -> EmbeddingFactory:
        return self._factory

    async def run(
        self,
        chunks: list[Chunk],
        provider: str | None = None,
        config: EmbeddingConfiguration | None = None,
        enable_validation: bool = True,
        **kwargs: Any,
    ) -> EmbeddingResult:
        """Run the full embedding pipeline.

        Args:
            chunks: Source ``Chunk`` objects to embed.
            provider: Provider name override.  Defaults to config's provider.
            config: Override configuration for this run.
            enable_validation: Run post-embedding validation.
            **kwargs: Additional keyword args forwarded to provider
                     configuration.

        Returns:
            An ``EmbeddingResult`` with embedded chunks and statistics.
        """
        start_time = time.monotonic()

        # Resolve configuration
        cfg = self._base_config
        if config:
            cfg = config
        if kwargs:
            cfg = cfg.merge(kwargs)

        provider_name = provider or cfg.provider

        # Get provider
        try:
            embedder = self._factory.create(provider_name)
        except Exception as exc:
            return EmbeddingResult(
                embeddings=[],
                errors=[f"Failed to create provider '{provider_name}': {exc}"],
                successful=False,
            )

        # Configure provider from config
        embedder.configure(cfg.extra)

        if not chunks:
            return EmbeddingResult(
                embeddings=[],
                warnings=["No chunks provided"],
                successful=True,
            )

        # Step 1: before_embedding hooks
        try:
            chunks = self._hooks.run_before_embedding(chunks)
        except Exception:
            logger.exception("before_embedding hooks failed")

        # Step 2: Split into batches
        batch_size = cfg.batch_size
        batches = [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]

        all_embeddings: list[EmbeddedChunk] = []
        model_name = embedder.model_name
        provider_name_str = embedder.provider_name
        dims = embedder.dimensions

        # Step 3: Process each batch
        for batch_idx, batch in enumerate(batches):
            # before_batch hooks
            try:
                batch = self._hooks.run_before_batch(batch)
            except Exception as exc:
                logger.exception("before_batch hooks failed: %s", exc)
                continue

            texts = [c.text for c in batch]
            try:
                vectors = await embedder.embed_batch(texts)
            except Exception as exc:
                error_msg = f"Batch {batch_idx} embedding failed: {exc}"
                logger.exception(error_msg)
                for chunk in batch:
                    all_embeddings.append(
                        EmbeddedChunk(
                            chunk_id=chunk.chunk_id,
                            vector=EmbeddingVector(vector=[], dimensions=0),
                            embedding_model=model_name,
                            embedding_provider=provider_name_str,
                            dimensions=0,
                            metadata=EmbeddingMetadata(
                                provider=provider_name_str,
                                model=model_name,
                                batch_index=batch_idx,
                                chunk_text_length=len(chunk.text),
                                extra={"error": error_msg},
                            ),
                        )
                    )
                continue

            batch_embeddings: list[EmbeddedChunk] = []
            for chunk, vec in zip(batch, vectors, strict=False):
                ec = EmbeddedChunk(
                    chunk_id=chunk.chunk_id,
                    vector=EmbeddingVector(vector=vec, dimensions=len(vec)),
                    embedding_model=model_name,
                    embedding_provider=provider_name_str,
                    dimensions=len(vec),
                    metadata=EmbeddingMetadata(
                        provider=provider_name_str,
                        model=model_name,
                        batch_index=batch_idx,
                        chunk_text_length=len(chunk.text),
                    ),
                )
                batch_embeddings.append(ec)

            # after_batch hooks
            try:
                batch_embeddings = self._hooks.run_after_batch(batch, batch_embeddings)
            except Exception as exc:
                logger.exception("after_batch hooks failed: %s", exc)

            all_embeddings.extend(batch_embeddings)

        result = EmbeddingResult(embeddings=all_embeddings)

        # Step 4: Validation
        if enable_validation and self._validation:
            vr = self._validation.validate(result)
            if vr.errors:
                result.errors.extend(vr.errors)
                result.successful = False
            for w in vr.warnings:
                if w not in result.warnings:
                    result.warnings.append(w)

        # Step 5: after_embedding hooks
        try:
            result = self._hooks.run_after_embedding(result)
        except Exception as exc:
            logger.exception("after_embedding hooks failed: %s", exc)

        # Step 6: Populate statistics
        elapsed = time.monotonic() - start_time
        n_chunks = len(all_embeddings)
        n_batches = len(batches) if batches else 0

        result.statistics.total_chunks = n_chunks
        result.statistics.total_batches = n_batches
        result.statistics.average_batch_size = n_chunks / n_batches if n_batches else 0
        result.statistics.total_processing_time = elapsed
        result.statistics.embedding_latency = elapsed / n_batches if n_batches else 0
        result.statistics.throughput = n_chunks / elapsed if elapsed > 0 else 0
        result.statistics.dimensions = dims
        result.statistics.model_name = model_name
        result.statistics.provider_name = provider_name_str

        return result
