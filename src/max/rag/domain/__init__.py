"""RAG Domain Package."""

from max.rag.domain.chunk import DocumentChunk
from max.rag.domain.document import Document, DocumentSource
from max.rag.domain.embedding import EmbeddingModelInfo, EmbeddingVector
from max.rag.domain.enums import DocumentSourceType, DocumentStatus, DocumentType
from max.rag.domain.exceptions import (
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
from max.rag.domain.query import RetrievalFilter, RetrievalQuery
from max.rag.domain.result import Citation, RetrievalResponse, RetrievalResult

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
