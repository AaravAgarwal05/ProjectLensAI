"""Chunking pipeline — orchestrates chunking lifecycle.

The pipeline wires together:
1. Pre-validation (document sanity checks).
2. ``before_chunking`` hooks.
3. The chunker (resolved via ``ChunkingFactory``).
4. ``after_chunking`` hooks.
5. Post-chunking validation (via ``ValidationEngine``).
6. ``after_validation`` hooks.

Each step is optional — hooks and validation can be omitted.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from shared.models.processing import ParsedDocument

from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.factory import ChunkingFactory
from src.ai_core.chunking.hooks import HookRegistry
from src.ai_core.chunking.models import ChunkingResult
from src.ai_core.chunking.validation import ValidationEngine

logger = logging.getLogger(__name__)


class ChunkingPipeline:
    """Orchestrates the chunking lifecycle with hooks and validation.

    Typical usage::

        pipeline = ChunkingPipeline(factory)
        result = pipeline.run(document, "heading_aware")

    With hooks::

        pipeline.hooks.register(HookEvent.BEFORE_CHUNKING, my_hook_fn)
        result = pipeline.run(document, "recursive")
    """

    def __init__(
        self,
        factory: ChunkingFactory | None = None,
        config: ChunkingConfiguration | None = None,
        hooks: HookRegistry | None = None,
        validation: ValidationEngine | None = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            factory: A ``ChunkingFactory``.  If ``None``, a default
                     factory (with all built-in strategies) is created.
            config: Optional base ``ChunkingConfiguration``.  Passed to
                    ``chunker.configure()`` before each run.
            hooks: An optional ``HookRegistry``.  A new empty one is
                   created if omitted.
            validation: An optional ``ValidationEngine``.  If omitted,
                        validation is skipped unless ``enable_validation``
                        is set on ``run()``.
        """
        self._factory = factory or ChunkingFactory()
        self._base_config = config
        self._hooks = hooks or HookRegistry()
        self._validation = validation

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def hooks(self) -> HookRegistry:
        """Access the pipeline's hook registry."""
        return self._hooks

    @property
    def factory(self) -> ChunkingFactory:
        """Access the pipeline's chunking factory."""
        return self._factory

    # ------------------------------------------------------------------
    # Pipeline execution
    # ------------------------------------------------------------------

    def run(
        self,
        document: ParsedDocument,
        strategy: str = "heading_aware",
        config: ChunkingConfiguration | None = None,
        enable_validation: bool = True,
        **kwargs: Any,
    ) -> ChunkingResult:
        """Run the full chunking pipeline.

        Args:
            document: The parsed document to chunk.
            strategy: Strategy name (``"heading_aware"``, ``"recursive"``,
                      ``"fixed"``).  Default ``"heading_aware"``.
            config: Override configuration for this run.  Merged with
                    the base config if both are set.
            enable_validation: Run post-chunking validation.
            **kwargs: Additional keyword arguments forwarded to the
                      chunker's ``configure()``.

        Returns:
            A ``ChunkingResult`` with chunks, statistics, and any
            warnings or errors.
        """
        start_time = time.monotonic()

        # Step 0: Resolve configuration
        cfg = self._base_config
        if config:
            cfg = config
        if kwargs:
            cfg = cfg.merge(kwargs) if cfg else ChunkingConfiguration(**kwargs)

        # Step 1: Get the chunker
        try:
            chunker = self._factory.create(strategy)
        except Exception as exc:
            return ChunkingResult(
                chunks=[],
                errors=[f"Failed to create chunker '{strategy}': {exc}"],
                successful=False,
            )

        # Step 2: Configure the chunker
        if cfg is not None:
            try:
                chunker.configure(cfg.extra)
            except Exception as exc:
                logger.warning("Chunker configure() failed: %s", exc)

        # Step 3: Pre-validation
        warnings: list[str] = []
        try:
            warnings = chunker.validate(document)
        except Exception as exc:
            return ChunkingResult(
                chunks=[],
                errors=[f"Pre-validation failed: {exc}"],
                successful=False,
            )

        if not document.clean_text:
            return ChunkingResult(
                chunks=[],
                warnings=warnings,
                errors=["Document has no clean_text content"],
                successful=False,
            )

        # Step 4: before_chunking hooks
        try:
            document = self._hooks.run_before_chunking(document)
        except Exception as exc:
            logger.exception("before_chunking hooks failed")
            warnings.append(f"before_chunking hook error: {exc}")

        # Step 5: Chunk
        try:
            result = chunker.chunk(document)
        except Exception as exc:
            return ChunkingResult(
                chunks=[],
                warnings=warnings,
                errors=[f"Chunking failed: {exc}"],
                successful=False,
            )

        # Merge pre-chunking warnings
        for w in warnings:
            if w not in result.warnings:
                result.warnings.append(w)

        # Step 6: after_chunking hooks
        try:
            result = self._hooks.run_after_chunking(result)
        except Exception as exc:
            logger.exception("after_chunking hooks failed")
            result.warnings.append(f"after_chunking hook error: {exc}")

        # Step 7: Validation
        if enable_validation and self._validation:
            try:
                result = self._hooks.run_before_validation(result)
            except Exception as exc:
                logger.exception("before_validation hooks failed")
                result.warnings.append(f"before_validation hook error: {exc}")

            try:
                vr = self._validation.validate(result)
                if vr.errors:
                    result.errors.extend(vr.errors)
                    result.successful = False
                if vr.warnings:
                    for w in vr.warnings:
                        if w not in result.warnings:
                            result.warnings.append(w)
            except Exception as exc:
                logger.exception("Validation failed")
                result.errors.append(f"Validation error: {exc}")
                result.successful = False

            try:
                result = self._hooks.run_after_validation(result)
            except Exception as exc:
                logger.exception("after_validation hooks failed")
                result.warnings.append(f"after_validation hook error: {exc}")

        # Step 8: Populate timing
        elapsed = time.monotonic() - start_time
        result.statistics.processing_time = elapsed

        return result
