"""API Request schemas for RAG & Retrieval Engine."""

from typing import Any

from pydantic import BaseModel, Field

from max.rag.domain.enums import DocumentSourceType, DocumentStatus, DocumentType


class SourcePayload(BaseModel):
    """Source provenance payload for API requests."""

    source_type: DocumentSourceType = Field(
        default=DocumentSourceType.TEXT, description="Provenance source category"
    )
    source_reference: str = Field(description="Unique reference identifier")
    uri: str | None = Field(default=None, description="Optional URI reference")


class DocumentCreateRequest(BaseModel):
    """Request payload for creating a document."""

    owner_id: str = Field(description="Owner user identifier")
    title: str = Field(description="Document title")
    content: str = Field(description="Document text payload")
    source: SourcePayload = Field(description="Source provenance information")
    document_type: DocumentType = Field(
        default=DocumentType.TEXT, description="Document type taxonomy"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary safe metadata key-values"
    )


class DocumentUpdateRequest(BaseModel):
    """Request payload for updating a document."""

    title: str | None = Field(default=None, description="Optional updated title")
    content: str | None = Field(default=None, description="Optional updated content text")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional updated metadata"
    )
    reindex: bool = Field(default=True, description="Whether to trigger automatic reindexing")


class FilterPayload(BaseModel):
    """Metadata filter payload for search requests."""

    document_type: DocumentType | list[DocumentType] | None = Field(
        default=None, description="Filter by document type(s)"
    )
    source_type: DocumentSourceType | list[DocumentSourceType] | None = Field(
        default=None, description="Filter by source type(s)"
    )
    document_id: str | list[str] | None = Field(
        default=None, description="Filter by document ID(s)"
    )
    collection_id: str | None = Field(default=None, description="Filter by collection ID")
    tags: list[str] | None = Field(default=None, description="Filter by tags")
    status: DocumentStatus | list[DocumentStatus] | None = Field(
        default=None, description="Filter by status"
    )


class RetrievalSearchRequest(BaseModel):
    """Request payload for executing vector retrieval search."""

    query_text: str = Field(description="Search query string")
    owner_id: str = Field(description="Owner user identifier")
    top_k: int = Field(default=5, description="Maximum results count (1 to 50)", ge=1, le=50)
    minimum_score: float = Field(
        default=0.0, description="Minimum relevance threshold (0.0 to 1.0)", ge=0.0, le=1.0
    )
    filters: FilterPayload = Field(
        default_factory=FilterPayload, description="Metadata filtering parameters"
    )
    include_archived: bool = Field(
        default=False, description="Whether to include ARCHIVED documents"
    )
    include_deleted: bool = Field(
        default=False, description="Whether to include DELETED documents"
    )
