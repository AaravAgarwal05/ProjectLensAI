"""Exception hierarchy for the document processing framework.

Every exception in this module uses a unique ``code`` string that callers
can rely on for programmatic error handling.
"""

from src.api.exceptions import ProjectLensError


class ProcessingError(ProjectLensError):
    """Base exception for all document-processing errors."""

    def __init__(
        self,
        message: str = "A document-processing error occurred",
        code: str = "processing_error",
        **kwargs: object,
    ) -> None:
        super().__init__(message=message, code=code, **kwargs)


class ParseError(ProcessingError):
    """Raised when a document cannot be parsed successfully."""

    def __init__(
        self,
        message: str = "Failed to parse document",
        code: str = "parse_error",
        **kwargs: object,
    ) -> None:
        super().__init__(message=message, code=code, **kwargs)


class CleanError(ProcessingError):
    """Raised when the cleaning stage fails."""

    def __init__(
        self,
        message: str = "Failed to clean document content",
        code: str = "clean_error",
        **kwargs: object,
    ) -> None:
        super().__init__(message=message, code=code, **kwargs)


class MetadataError(ProcessingError):
    """Raised when metadata extraction fails."""

    def __init__(
        self,
        message: str = "Failed to extract document metadata",
        code: str = "metadata_error",
        **kwargs: object,
    ) -> None:
        super().__init__(message=message, code=code, **kwargs)


class ParserNotFoundError(ProcessingError):
    """Raised when no parser is registered for a given format."""

    def __init__(
        self,
        message: str = "No parser registered for the requested format",
        code: str = "parser_not_found",
        **kwargs: object,
    ) -> None:
        super().__init__(message=message, code=code, **kwargs)


class CleanerNotFoundError(ProcessingError):
    """Raised when no cleaner is registered under a given name."""

    def __init__(
        self,
        message: str = "No cleaner registered for the requested name",
        code: str = "cleaner_not_found",
        **kwargs: object,
    ) -> None:
        super().__init__(message=message, code=code, **kwargs)
