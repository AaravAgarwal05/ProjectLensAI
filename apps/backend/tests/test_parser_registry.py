"""Tests for ParserRegistry — mapping file formats to parser implementations."""

from __future__ import annotations

import pytest

from shared.models.processing import ParsedDocument
from src.document_processing.exceptions import ParserNotFoundError
from src.document_processing.parsers.base import BaseParser
from src.document_processing.parsers.registry import ParserRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_parser_cls(name: str, formats: list[str]) -> type[BaseParser]:
    """Return a concrete BaseParser subclass with fixed *name* and *formats*."""
    class _ConcreteParser(BaseParser):
        @property
        def name(self) -> str:
            return name

        @classmethod
        def supported_formats(cls) -> list[str]:
            return formats

        async def parse(self, file_path: str) -> ParsedDocument:
            return ParsedDocument(parser_used=name)

    return _ConcreteParser


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestParserRegistry:
    """Suite for ParserRegistry."""

    def test_register_and_get_parser(self) -> None:
        """Register a parser and retrieve a cached instance for its format."""
        registry = ParserRegistry()
        pdf_cls = _make_parser_cls("pdf", ["pdf"])
        registry.register(pdf_cls)

        parser = registry.get("pdf")

        assert parser is not None
        assert parser.name == "pdf"

    def test_get_nonexistent_parser_raises(self) -> None:
        """Getting a parser for an unregistered format raises ParserNotFoundError."""
        registry = ParserRegistry()

        with pytest.raises(ParserNotFoundError) as exc_info:
            registry.get("bogus")

        assert "bogus" in str(exc_info.value).lower()

    def test_list_formats(self) -> None:
        """List all registered format extension strings."""
        registry = ParserRegistry()
        registry.register(_make_parser_cls("pdf", ["pdf"]))
        registry.register(_make_parser_cls("docx", ["docx"]))
        registry.register(_make_parser_cls("text", ["txt", "md", "csv"]))

        formats = registry.list_formats()
        assert sorted(formats) == ["csv", "docx", "md", "pdf", "txt"]

    def test_register_same_format_replaces(self) -> None:
        """Registering a second parser for the same format replaces the first."""
        registry = ParserRegistry()
        old_cls = _make_parser_cls("old_pdf", ["pdf"])
        new_cls = _make_parser_cls("new_pdf", ["pdf"])

        registry.register(old_cls)
        registry.register(new_cls)

        parser = registry.get("pdf")
        assert parser.name == "new_pdf"
