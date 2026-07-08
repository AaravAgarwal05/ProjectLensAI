"""Tests for CleanerRegistry — mapping names to cleaner implementations."""

from __future__ import annotations

import pytest

from src.document_processing.cleaners.base import TextCleaner
from src.document_processing.cleaners.registry import CleanerRegistry
from src.document_processing.exceptions import CleanerNotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cleaner_cls(name: str) -> type[TextCleaner]:
    """Return a concrete TextCleaner subclass with fixed *name*."""
    class _ConcreteCleaner(TextCleaner):
        @property
        def name(self) -> str:
            return name

        def clean(self, text: str) -> str:
            return f"[{name}]{text}[{name}]"

    return _ConcreteCleaner


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCleanerRegistry:
    """Suite for CleanerRegistry."""

    def test_register_and_get_cleaner(self) -> None:
        """Register a cleaner and retrieve a cached instance."""
        registry = CleanerRegistry()
        cls = _make_cleaner_cls("strip_html")

        registry.register("strip_html", cls)
        cleaner = registry.get("strip_html")

        assert cleaner is not None
        assert cleaner.name == "strip_html"
        assert cleaner.clean("hello") == "[strip_html]hello[strip_html]"

    def test_create_pipeline_in_order(self) -> None:
        """create_pipeline composes cleaners in the requested order."""
        registry = CleanerRegistry()
        registry.register("a", _make_cleaner_cls("a"))
        registry.register("b", _make_cleaner_cls("b"))
        registry.register("c", _make_cleaner_cls("c"))

        pipeline = registry.create_pipeline(["a", "b", "c"])
        result = pipeline.run("x")

        # Each cleaner wraps in its own tag; order is a then b then c.
        assert result == "[c][b][a]x[a][b][c]"

    def test_get_nonexistent_cleaner_raises(self) -> None:
        """Getting a cleaner that was never registered raises CleanerNotFoundError."""
        registry = CleanerRegistry()

        with pytest.raises(CleanerNotFoundError) as exc_info:
            registry.get("never_registered")

        assert "never_registered" in str(exc_info.value).lower()
