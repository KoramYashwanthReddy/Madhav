"""Document domain model for RAG & Retrieval Engine."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from max.rag.domain.enums import DocumentSourceType, DocumentStatus, DocumentType
from max.rag.domain.exceptions import DocumentValidationError


class DocumentSource(BaseModel):
    """Provenance source representation for a document."""

    source_type: DocumentSourceType = Field(description="Provenance source category")
    source_reference: str = Field(description="Unique reference identifier for source")
    uri: str | None = Field(default=None, description="Optional URI or path reference")


class Document(BaseModel):
    """Domain model representing an indexed source document."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Document unique identifier")
    owner_id: str = Field(description="Owner user identifier")
    title: str = Field(description="Document title or display name")
    content: str = Field(description="Normalized document text content")
    source: DocumentSource = Field(description="Document provenance source info")
    document_type: DocumentType = Field(
        default=DocumentType.TEXT, description="Document content format type"
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.ACTIVE, description="Document indexing lifecycle state"
    )
    content_hash: str = Field(description="SHA-256 hash of document content for change tracking")
    metadata: dict[str, str | int | float | bool | list[str]] = Field(
        default_factory=dict, description="Arbitrary safe document metadata key-values"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last modification timestamp"
    )
    indexed_at: datetime | None = Field(
        default=None, description="Timestamp when successfully indexed"
    )

    def transition_to(self, new_status: DocumentStatus) -> None:
        """Validate and apply a lifecycle status transition."""
        if self.status == new_status:
            return

        valid_transitions: dict[DocumentStatus, set[DocumentStatus]] = {
            DocumentStatus.ACTIVE: {
                DocumentStatus.INDEXING,
                DocumentStatus.ARCHIVED,
                DocumentStatus.DELETED,
            },
            DocumentStatus.INDEXING: {
                DocumentStatus.INDEXED,
                DocumentStatus.FAILED,
            },
            DocumentStatus.INDEXED: {
                DocumentStatus.INDEXING,
                DocumentStatus.ARCHIVED,
                DocumentStatus.DELETED,
            },
            DocumentStatus.FAILED: {
                DocumentStatus.INDEXING,
                DocumentStatus.DELETED,
            },
            DocumentStatus.ARCHIVED: {
                DocumentStatus.ACTIVE,
                DocumentStatus.DELETED,
            },
            DocumentStatus.DELETED: set(),  # Terminal state
        }

        allowed = valid_transitions.get(self.status, set())
        if new_status not in allowed:
            raise DocumentValidationError(
                f"Invalid document status transition from '{self.status}' to '{new_status}'.",
                details={
                    "document_id": self.id,
                    "current_status": self.status,
                    "target_status": new_status,
                },
            )

        self.status = new_status
        self.updated_at = datetime.now(UTC)
        if new_status == DocumentStatus.INDEXED:
            self.indexed_at = datetime.now(UTC)
