"""Base parser interface for Module 24 — Document Intelligence."""

from abc import ABC, abstractmethod
from typing import Any

from max.document.domain.enums import DocumentFormat
from max.document.domain.models import DocumentExtractionResult


class BaseDocumentParser(ABC):
    """Provider-neutral abstract interface for document parsers."""

    @property
    @abstractmethod
    def supported_formats(self) -> list[DocumentFormat]:
        """Return list of DocumentFormats supported by this parser instance."""

    def supports(self, fmt: DocumentFormat) -> bool:
        """Return True if this parser supports the specified format."""
        return fmt in self.supported_formats

    @abstractmethod
    def parse(
        self,
        document_id: str,
        version_id: str,
        content_bytes: bytes,
        filename: str,
        source_reference: str = "",
    ) -> DocumentExtractionResult:
        """Parse raw document bytes into a normalized DocumentExtractionResult."""
