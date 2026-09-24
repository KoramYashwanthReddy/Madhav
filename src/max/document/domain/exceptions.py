"""Domain exceptions for Module 24 — Document Intelligence."""

from typing import Any


class DocumentError(Exception):
    """Base exception for all Document Intelligence errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsupportedDocumentFormatError(DocumentError):
    """Raised when an unrecognized or unsupported document format is encountered."""


class DocumentNotFoundError(DocumentError):
    """Raised when a requested Document or DocumentVersion cannot be found."""


class DocumentTooLargeError(DocumentError):
    """Raised when a document exceeds maximum allowed file size or page/element limits."""


class DocumentParseError(DocumentError):
    """Raised when document parsing fails due to corruption or formatting errors."""


class DocumentValidationError(DocumentError):
    """Raised when extraction or generation validation checks fail."""


class DocumentSecurityError(DocumentError):
    """Raised when document content violates security boundaries (XXE, prompt injection, forbidden paths)."""


class DocumentProcessingTimeoutError(DocumentError):
    """Raised when document processing exceeds maximum allowed execution duration."""


class DocumentProcessingCancelledError(DocumentError):
    """Raised when a document processing job is cancelled."""


class DocumentVersionConflictError(DocumentError):
    """Raised when a version collision or concurrency conflict occurs."""


class DocumentGenerationError(DocumentError):
    """Raised when document generation fails."""


class DocumentConversionError(DocumentError):
    """Raised when document conversion fails."""
