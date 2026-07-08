"""Text cleaners, composite pipeline, and cleaner registry.

Exports
-------
- ``TextCleaner`` — abstract interface every cleaner must implement.
- ``CleanerRegistry`` — maps names to cleaner classes (lazy instantiation).
- ``WhitespaceCleaner`` — collapse excessive whitespace.
- ``UnicodeCleaner`` — NFKC normalisation + typographic replacements.
- ``PageArtifactCleaner`` — strip page-number / header / footer artefacts.
- ``CleaningPipeline`` — compose cleaners and run them in sequence.
"""

from src.document_processing.cleaners.artifacts import PageArtifactCleaner
from src.document_processing.cleaners.base import CleaningPipeline, TextCleaner
from src.document_processing.cleaners.registry import CleanerRegistry
from src.document_processing.cleaners.unicode import UnicodeCleaner
from src.document_processing.cleaners.whitespace import WhitespaceCleaner

__all__ = [
    "CleanerRegistry",
    "CleaningPipeline",
    "PageArtifactCleaner",
    "TextCleaner",
    "UnicodeCleaner",
    "WhitespaceCleaner",
]
