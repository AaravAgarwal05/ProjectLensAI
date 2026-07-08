"""Tests for individual cleaners and the composite CleaningPipeline."""

from __future__ import annotations

from src.document_processing.cleaners.artifacts import PageArtifactCleaner
from src.document_processing.cleaners.base import CleaningPipeline
from src.document_processing.cleaners.unicode import UnicodeCleaner
from src.document_processing.cleaners.whitespace import WhitespaceCleaner


class TestWhitespaceCleaner:
    """WhitespaceCleaner normalisation behaviour."""

    def test_whitespace_cleaner_collapses_spaces(self) -> None:
        """Multiple consecutive spaces are collapsed into one."""
        cleaner = WhitespaceCleaner()
        result = cleaner.clean("hello     world   here")
        assert result == "hello world here"

    def test_whitespace_cleaner_normalizes_newlines(self) -> None:
        """3+ consecutive newlines are collapsed to 2; leading/trailing stripped."""
        text = "\n\n\n\nline1\n\n\n\n\nline2\n\n\n"
        result = WhitespaceCleaner().clean(text)
        # Two blank lines max between content lines; stripped at ends.
        assert result == "line1\n\nline2"


class TestUnicodeCleaner:
    """UnicodeCleaner normalisation and typographic replacement."""

    def test_unicode_cleaner_normalizes_nfkc(self) -> None:
        """NFKC normalisation is applied (e.g. fullwidth chars → ASCII)."""
        cleaner = UnicodeCleaner()
        # Fullwidth Latin letters (U+FF21 = A)
        result = cleaner.clean("ＡＢＣ")
        # NFKC normalises fullwidth to ASCII
        assert result == "ABC"

    def test_unicode_cleaner_replaces_smart_quotes(self) -> None:
        """Curly quotes, en/em dashes, ellipsis are replaced with ASCII equivalents."""
        cleaner = UnicodeCleaner()
        text = (
            "“Hello” ‘world’ – — …"
        )
        result = cleaner.clean(text)
        assert '"' in result  # left/right double quote → "
        assert "'" in result  # left/right single quote → '
        assert "--" in result or "-" in result  # em dash → --
        assert "..." in result  # ellipsis → ...


class TestPageArtifactCleaner:
    """PageArtifactCleaner removal of page numbers and repeated headers/footers."""

    def test_page_artifact_cleaner_removes_page_numbers(self) -> None:
        """Standalone page-number lines are removed."""
        cleaner = PageArtifactCleaner()
        text = "Some content\n\n- 42 -\n\nMore content"
        result = cleaner.clean(text)
        assert "42" not in result

    def test_page_artifact_cleaner_removes_page_x_of_y(self) -> None:
        """'Page N of M' lines are removed."""
        cleaner = PageArtifactCleaner()
        text = "Content\nPage 3 of 10\nMore content"
        result = cleaner.clean(text)
        assert "Page 3 of 10" not in result


class TestCleaningPipeline:
    """Composite CleaningPipeline applies all cleaners in order."""

    def test_cleaning_pipeline_applies_all_cleaners(self) -> None:
        """The pipeline runs each cleaner sequentially on the input."""
        pipeline = CleaningPipeline([
            WhitespaceCleaner(),
            UnicodeCleaner(),
            PageArtifactCleaner(),
        ])
        # Text with multiple issues: extra spaces, smart quotes, and a page number.
        text = 'This  is   “test”    content\n\n- 5 -\n\nMore  stuff'
        result = pipeline.run(text)

        # Whitespace collapsed, smart quotes replaced, page number removed.
        assert "  " not in result
        assert "“" not in result
        assert "- 5 -" not in result or "5" not in result
        assert result.startswith("This")
        assert result.endswith("stuff")
