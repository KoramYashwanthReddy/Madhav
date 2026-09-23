"""Domain exceptions for RAG & Retrieval Engine."""

from typing import Any

from madhav.core.exceptions import MadhavException


class RAGError(MadhavException):
    """Base exception for RAG & Retrieval subsystem."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="RAG_ERROR", details=details)


class DocumentNotFoundError(RAGError):
    """Raised when requested document is not found."""

    def __init__(self, document_id: str) -> None:
        super().__init__(
            f"Document with ID '{document_id}' was not found.",
            details={"document_id": document_id},
        )


class DocumentValidationError(RAGError):
    """Raised when document payload or transition validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class DocumentIndexingError(RAGError):
    """Raised when indexing document pipeline fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class EmbeddingProviderError(RAGError):
    """Raised when embedding provider computation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class EmbeddingDimensionMismatchError(RAGError):
    """Raised when vector dimensions do not match expected provider dimensions."""

    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(
            f"Embedding dimension mismatch: expected {expected}, got {actual}.",
            details={"expected": expected, "actual": actual},
        )


class VectorStoreError(RAGError):
    """Raised when vector store operation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class RetrievalValidationError(RAGError):
    """Raised when retrieval query validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class RetrievalError(RAGError):
    """Raised when retrieval search execution fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class UnsupportedDocumentTypeError(RAGError):
    """Raised when document type is unsupported."""

    def __init__(self, document_type: str) -> None:
        super().__init__(
            f"Unsupported document type: '{document_type}'.",
            details={"document_type": document_type},
        )
