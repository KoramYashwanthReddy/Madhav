"""Retrieval Query domain model for RAG & Retrieval Engine."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from max.rag.domain.enums import DocumentSourceType, DocumentStatus, DocumentType
from max.rag.domain.exceptions import RetrievalValidationError


class RetrievalFilter(BaseModel):
    """Metadata filter criteria for vector similarity queries."""

    owner_id: str | None = Field(default=None, description="Filter by owner user ID")
    document_type: DocumentType | list[DocumentType] | None = Field(
        default=None, description="Filter by document type(s)"
    )
    source_type: DocumentSourceType | list[DocumentSourceType] | None = Field(
        default=None, description="Filter by provenance source type(s)"
    )
    document_id: str | list[str] | None = Field(
        default=None, description="Filter by specific document ID(s)"
    )
    collection_id: str | None = Field(default=None, description="Filter by collection identifier")
    tags: list[str] | None = Field(default=None, description="Filter by metadata tags")
    status: DocumentStatus | list[DocumentStatus] | None = Field(
        default=None, description="Filter by document lifecycle status"
    )
    created_after: datetime | None = Field(
        default=None, description="Filter documents created after timestamp"
    )
    created_before: datetime | None = Field(
        default=None, description="Filter documents created before timestamp"
    )


class RetrievalQuery(BaseModel):
    """Domain model representing a structured retrieval query request."""

    query_text: str = Field(description="Search query string")
    owner_id: str = Field(description="Owner user identifier making the query")
    top_k: int = Field(default=5, description="Maximum number of results to retrieve")
    minimum_score: float = Field(
        default=0.0, description="Minimum relevance threshold score (0.0 to 1.0)"
    )
    filters: RetrievalFilter = Field(
        default_factory=RetrievalFilter, description="Metadata filtering parameters"
    )
    source_types: list[DocumentSourceType] | None = Field(
        default=None, description="Convenience filter for source types"
    )
    document_types: list[DocumentType] | None = Field(
        default=None, description="Convenience filter for document types"
    )
    include_archived: bool = Field(
        default=False, description="Whether to include ARCHIVED documents"
    )
    include_deleted: bool = Field(
        default=False, description="Whether to include DELETED documents"
    )

    @model_validator(mode="after")
    def validate_query_fields(self) -> "RetrievalQuery":
        """Validate search parameters."""
        stripped = self.query_text.strip()
        if not stripped:
            raise RetrievalValidationError("Retrieval query_text cannot be empty or blank.")

        if self.top_k <= 0:
            raise RetrievalValidationError(
                f"Invalid top_k: {self.top_k}. Must be a positive integer.",
                details={"top_k": self.top_k},
            )

        if not (0.0 <= self.minimum_score <= 1.0):
            raise RetrievalValidationError(
                f"Invalid minimum_score: {self.minimum_score}. Must be between 0.0 and 1.0.",
                details={"minimum_score": self.minimum_score},
            )

        return self
