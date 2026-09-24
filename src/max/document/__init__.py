"""Module 24 — Document Intelligence.

Provides structured understanding of documents:
 - Multi-format parsing (PDF, DOCX, XLSX, PPTX, TXT, MD, CSV, JSON, XML)
 - Metadata & structural extraction
 - Security-wrapped content (prompt injection defense, XXE protection)
 - Deterministic search with citations
 - Document comparison (diff)
 - RAG chunk preparation for Module 10
 - Document generation and conversion
 - Full audit trail and version history
"""

from max.document.container import DocumentContainer, get_document_container, reset_document_container
from max.document.domain.enums import (
    ComparisonChangeType,
    DocumentFormat,
    DocumentSource,
    DocumentStatus,
    DocumentType,
    ElementType,
    ProcessingStatus,
)
from max.document.domain.exceptions import (
    DocumentConversionError,
    DocumentError,
    DocumentGenerationError,
    DocumentNotFoundError,
    DocumentParseError,
    DocumentProcessingCancelledError,
    DocumentProcessingTimeoutError,
    DocumentSecurityError,
    DocumentTooLargeError,
    DocumentValidationError,
    DocumentVersionConflictError,
    UnsupportedDocumentFormatError,
)
from max.document.domain.models import (
    Document,
    DocumentChange,
    DocumentCitation,
    DocumentComparison,
    DocumentConversionRequest,
    DocumentConversionResult,
    DocumentElement,
    DocumentExtractionResult,
    DocumentGenerationRequest,
    DocumentGenerationResult,
    DocumentHeading,
    DocumentList,
    DocumentLocation,
    DocumentMetadata,
    DocumentPage,
    DocumentParagraph,
    DocumentProcessingError,
    DocumentProcessingJob,
    DocumentProvenance,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchResult,
    DocumentSection,
    DocumentSheet,
    DocumentSlide,
    DocumentStructure,
    DocumentSummary,
    DocumentTable,
    DocumentTableCell,
    DocumentTableRow,
    DocumentValidationResult,
    DocumentVersion,
)
from max.document.services.document_service import DocumentService
from max.document.services.tool_integration import register_document_tools

__all__ = [
    # Container
    "DocumentContainer",
    "get_document_container",
    "reset_document_container",
    # Enums
    "ComparisonChangeType",
    "DocumentFormat",
    "DocumentSource",
    "DocumentStatus",
    "DocumentType",
    "ElementType",
    "ProcessingStatus",
    # Exceptions
    "DocumentConversionError",
    "DocumentError",
    "DocumentGenerationError",
    "DocumentNotFoundError",
    "DocumentParseError",
    "DocumentProcessingCancelledError",
    "DocumentProcessingTimeoutError",
    "DocumentSecurityError",
    "DocumentTooLargeError",
    "DocumentValidationError",
    "DocumentVersionConflictError",
    "UnsupportedDocumentFormatError",
    # Models
    "Document",
    "DocumentChange",
    "DocumentCitation",
    "DocumentComparison",
    "DocumentConversionRequest",
    "DocumentConversionResult",
    "DocumentElement",
    "DocumentExtractionResult",
    "DocumentGenerationRequest",
    "DocumentGenerationResult",
    "DocumentHeading",
    "DocumentList",
    "DocumentLocation",
    "DocumentMetadata",
    "DocumentPage",
    "DocumentParagraph",
    "DocumentProcessingError",
    "DocumentProcessingJob",
    "DocumentProvenance",
    "DocumentSearchRequest",
    "DocumentSearchResponse",
    "DocumentSearchResult",
    "DocumentSection",
    "DocumentSheet",
    "DocumentSlide",
    "DocumentStructure",
    "DocumentSummary",
    "DocumentTable",
    "DocumentTableCell",
    "DocumentTableRow",
    "DocumentValidationResult",
    "DocumentVersion",
    # Services
    "DocumentService",
    "register_document_tools",
]
