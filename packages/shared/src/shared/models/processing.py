"""Pydantic models for the document processing pipeline output (ParsedDocument and related types)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.main import BaseModel


class Page(BaseModel):
    """A single page extracted during document processing.

    Attributes:
        number: 1-indexed page number.
        content: Text content of the page.
        metadata: Arbitrary metadata key-value pairs for this page.
        char_count: Number of characters in the page content.
        word_count: Number of words in the page content.
    """

    number: int
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    char_count: int = 0
    word_count: int = 0


class DocumentMetadata(BaseModel):
    """Rich metadata extracted during document processing.

    Attributes:
        title: Human-readable document title (if detectable).
        author: Document author name (if detectable).
        subject: Document subject or topic.
        keywords: List of extracted or provided keywords.
        language: ISO language code (e.g. ``"en"``, ``"fr"``).
        page_count: Total number of pages detected.
        word_count: Total word count across all pages.
        char_count: Total character count across all pages.
        creation_date: Document creation timestamp (if embedded).
        modification_date: Document last-modified timestamp (if embedded).
        processed_by: Identifier of the processor that parsed this document.
        extra: Catch-all for any additional metadata not covered above.
    """

    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: list[str] = Field(default_factory=list)
    language: str | None = None
    page_count: int | None = None
    word_count: int = 0
    char_count: int = 0
    creation_date: datetime | None = None
    modification_date: datetime | None = None
    processed_by: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ProcessingWarning(BaseModel):
    """A non-fatal warning generated during a processing stage.

    Attributes:
        stage: The processing stage that generated the warning (e.g. ``"ocr"``, ``"clean"``).
        message: Human-readable warning description.
        details: Optional structured context about the warning.
    """

    stage: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ProcessingError(BaseModel):
    """A fatal error that occurred during a processing stage.

    Attributes:
        stage: The processing stage that generated the error.
        message: Human-readable error description.
        code: Machine-readable error code (e.g. ``"PARSE_FAILURE"``).
        details: Optional structured context about the error.
    """

    stage: str
    message: str
    code: str
    details: dict[str, Any] = Field(default_factory=dict)


class ProcessingStatistics(BaseModel):
    """Timing and sizing statistics for the processing pipeline run.

    Attributes:
        parse_time_ms: Time spent parsing the raw document (ms).
        clean_time_ms: Time spent cleaning / normalising text (ms).
        metadata_time_ms: Time spent extracting metadata (ms).
        total_time_ms: Total end-to-end processing time (ms).
        page_count: Number of pages processed.
        raw_char_count: Character count of the raw (uncleaned) text.
        clean_char_count: Character count after cleaning.
    """

    parse_time_ms: float = 0
    clean_time_ms: float = 0
    metadata_time_ms: float = 0
    total_time_ms: float = 0
    page_count: int = 0
    raw_char_count: int = 0
    clean_char_count: int = 0


class ParsedDocument(BaseModel):
    """The output of the ProcessingPipeline — a fully parsed and cleaned document.

    Attributes:
        report_id: Optional identifier for the originating report.
        version_id: Optional identifier for the specific version processed.
        parser_used: Name or identifier of the parser that produced this output.
        metadata: Extracted document-level metadata.
        pages: Ordered list of extracted pages.
        raw_text: Concatenated raw text before cleaning.
        clean_text: Concatenated cleaned / normalised text.
        warnings: Non-fatal warnings generated during processing.
        errors: Fatal errors generated during processing.
        statistics: Timing and sizing statistics for this processing run.
        created_at: Timestamp when this ParsedDocument was created.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    report_id: str | None = None
    version_id: str | None = None
    parser_used: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    pages: list[Page] = Field(default_factory=list)
    raw_text: str = ""
    clean_text: str = ""
    warnings: list[ProcessingWarning] = Field(default_factory=list)
    errors: list[ProcessingError] = Field(default_factory=list)
    statistics: ProcessingStatistics = Field(default_factory=ProcessingStatistics)
    created_at: datetime = Field(default_factory=datetime.utcnow)
