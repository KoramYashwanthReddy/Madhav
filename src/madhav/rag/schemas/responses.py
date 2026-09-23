"""API Response schemas for RAG & Retrieval Engine."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from madhav.rag.domain.enums import DocumentSourceType, DocumentStatus, DocumentType


class CitationResponse(BaseModel):
    """Citation metadata in search response."""

    document_id: str
    chunk_id: str
    source_type: DocumentSourceType
    source_reference: str
    title: str
    location: str | None = None
    score: float


class RetrievalResultResponse(BaseModel):
    """Individual match item in search response."""

    chunk_id: str
    document_id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, Any]
    citation: CitationResponse


class RetrievalSearchResponse(BaseModel):
    """Search query response model."""

    query_text: str
    owner_id: str
    results: list[RetrievalResultResponse]
    total_retrieved: int
    citations: list[CitationResponse]
    execution_time_ms: float
    metadata: dict[str, Any]


class DocumentResponse(BaseModel):
    """Single Document representation."""

    id: str
    owner_id: str
    title: str
    content: str
    source_type: DocumentSourceType
    source_reference: str
    document_type: DocumentType
    status: DocumentStatus
    content_hash: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None = None


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    documents: list[DocumentResponse]
    total: int
    skip: int
    limit: int


class RAGStatusResponse(BaseModel):
    """Subsystem status diagnostic payload."""

    rag_enabled: bool
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    vector_store_provider: str
    vector_store_health: dict[str, Any]
    default_top_k: int
    max_top_k: int
    minimum_score: float
