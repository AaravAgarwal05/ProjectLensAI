"""Parser abstractions, registry, and built-in implementations.

Exports
-------
- ``BaseParser`` — abstract interface every parser must implement.
- ``ParserRegistry`` — maps file extensions to parser classes (lazy
  instantiation). Not a singleton.
- ``PDFParser`` — placeholder for PDF parsing (PyMuPDF / pdfplumber).
- ``DOCXParser`` — placeholder for DOCX parsing (python-docx).
"""

from src.document_processing.parsers.base import BaseParser
from src.document_processing.parsers.docx import DOCXParser
from src.document_processing.parsers.pdf import PDFParser
from src.document_processing.parsers.registry import ParserRegistry

__all__ = [
    "BaseParser",
    "DOCXParser",
    "PDFParser",
    "ParserRegistry",
]
