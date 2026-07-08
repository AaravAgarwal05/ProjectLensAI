"""Document processing framework — plugin-based, registry-resolved.

Every component is interface-driven. Parsers and cleaners are registered
via their respective registries (``ParserRegistry``, ``CleanerRegistry``)
and resolved at runtime.

Exports
-------
- ``ProcessingPipeline`` — top-level orchestrator.
- ``ProcessingContext`` — mutable runtime state across pipeline stages.
- ``PipelineHook`` — base class for lifecycle hooks.
- ``ParsedDocument`` — structured output of the pipeline.
- ``ParserRegistry`` — maps file extensions to parser classes.
- ``CleanerRegistry`` — maps names to cleaner classes.
"""

from shared.models.processing import ParsedDocument

from src.document_processing.cleaners.registry import CleanerRegistry
from src.document_processing.metadata import MetadataExtractor
from src.document_processing.parsers.registry import ParserRegistry
from src.document_processing.pipeline import PipelineHook, ProcessingContext, ProcessingPipeline

__all__ = [
    "CleanerRegistry",
    "MetadataExtractor",
    "ParsedDocument",
    "ParserRegistry",
    "PipelineHook",
    "ProcessingContext",
    "ProcessingPipeline",
]
