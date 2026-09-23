"""RAG Domain Package."""

from madhav.rag.domain.chunk import DocumentChunk
from madhav.rag.domain.document import Document, DocumentSource
from madhav.rag.domain.embedding import EmbeddingModelInfo, EmbeddingVector
from madhav.rag.domain.enums import DocumentSourceType, DocumentStatus, DocumentType
from madhav.rag.domain.exceptions import (
    DocumentIndexingError,
    DocumentNotFoundError,
    DocumentValidationError,
    EmbeddingDimensionMismatchError,
    EmbeddingProviderError,
    RAGError,
    RetrievalError,
    RetrievalValidationError,
    UnsupportedDocumentTypeError,
    VectorStoreError,
)
from madhav.rag.domain.query import RetrievalFilter, RetrievalQuery
from madhav.rag.domain.result import Citation, RetrievalResponse, RetrievalResult

__all__ = [
    "Citation",
    "Document",
    "DocumentChunk",
    "DocumentIndexingError",
    "DocumentNotFoundError",
    "DocumentSource",
    "DocumentSourceType",
    "DocumentStatus",
    "DocumentType",
    "DocumentValidationError",
    "EmbeddingDimensionMismatchError",
    "EmbeddingModelInfo",
    "EmbeddingProviderError",
    "EmbeddingVector",
    "RAGError",
    "RetrievalError",
    "RetrievalFilter",
    "RetrievalQuery",
    "RetrievalResponse",
    "RetrievalResult",
    "RetrievalValidationError",
    "UnsupportedDocumentTypeError",
    "VectorStoreError",
]
