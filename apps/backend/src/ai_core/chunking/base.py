"""Abstract chunker interface.

Every chunking strategy implements ``ChunkingStrategy``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from shared.models.processing import ParsedDocument

from src.ai_core.chunking.models import ChunkingResult


class ChunkingStrategy(ABC):
    """Interface for document chunking strategies.

    Implementations are stateless strategies — they receive a
    ``ParsedDocument`` and return a ``ChunkingResult``.  Configuration
    is applied at construction time via ``ChunkingConfiguration``.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique chunker identifier (e.g. ``"fixed"``, ``"recursive"``)."""

    @abstractmethod
    def chunk(self, document: ParsedDocument) -> ChunkingResult:
        """Chunk a parsed document.

        Args:
            document: The output of the processing pipeline.

        Returns:
            A ``ChunkingResult`` containing chunks and statistics.
        """

    @abstractmethod
    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure the chunker at runtime.

        Args:
            params: Chunker-specific configuration keys and values.
        """

    @abstractmethod
    def validate(self, document: ParsedDocument) -> list[str]:
        """Pre-chunking validation.

        Returns a list of warning messages.  An empty list means the
        document is valid for this chunker.

        Args:
            document: The parsed document to validate.
        """
