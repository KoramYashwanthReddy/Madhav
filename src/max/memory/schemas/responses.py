"""API response DTO models for Memory Engine endpoints."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from max.memory.domain.duplicate import MemoryDuplicateResult
from max.memory.domain.memory import Memory
from max.memory.domain.summary import MemorySummary


class MemoryResponse(BaseModel):
    """API DTO representing a full Memory aggregate record."""

    memory_id: UUID = Field(description="Unique memory identifier")
    owner_id: str = Field(description="Owner identity identifier")
    type: str = Field(description="Memory type category string")
    text: str = Field(description="Text payload")
    structured_data: dict[str, Any] = Field(description="Structured data payload")
    content_type: str = Field(description="MIME content-type indicator")
    status: str = Field(description="Lifecycle status string")
    importance: str = Field(description="Importance rating string")
    confidence: str = Field(description="Confidence rating string")
    source: str = Field(description="Source origin indicator")
    scope: str = Field(description="Ownership scope")
    tags: list[str] = Field(description="Indexing tags")
    source_reference: str | None = Field(default=None, description="Source document reference")
    conversation_id: str | None = Field(default=None, description="Origin conversation ID")
    message_id: str | None = Field(default=None, description="Origin message ID")
    custom_metadata: dict[str, Any] = Field(description="Custom metadata attributes")
    created_at: str = Field(description="Creation UTC ISO timestamp")
    updated_at: str = Field(description="Update UTC ISO timestamp")
    last_accessed_at: str | None = Field(default=None, description="Last access UTC ISO timestamp")
    expires_at: str | None = Field(default=None, description="Expiration UTC ISO timestamp")
    archived_at: str | None = Field(default=None, description="Archived UTC ISO timestamp")
    deleted_at: str | None = Field(default=None, description="Deleted UTC ISO timestamp")

    @classmethod
    def from_domain(cls, memory: Memory) -> "MemoryResponse":
        """Construct DTO from domain Memory model."""
        return cls(
            memory_id=memory.memory_id,
            owner_id=memory.owner_id,
            type=memory.type.value,
            text=memory.content.text,
            structured_data=memory.content.structured_data,
            content_type=memory.content.content_type,
            status=memory.status.value,
            importance=memory.importance.value,
            confidence=memory.confidence.value,
            source=memory.source.value,
            scope=memory.scope.value,
            tags=memory.metadata.tags,
            source_reference=memory.metadata.source_reference,
            conversation_id=memory.metadata.conversation_id,
            message_id=memory.metadata.message_id,
            custom_metadata=memory.metadata.custom_metadata,
            created_at=memory.created_at.isoformat(),
            updated_at=memory.updated_at.isoformat(),
            last_accessed_at=memory.last_accessed_at.isoformat()
            if memory.last_accessed_at
            else None,
            expires_at=memory.expires_at.isoformat() if memory.expires_at else None,
            archived_at=memory.archived_at.isoformat() if memory.archived_at else None,
            deleted_at=memory.deleted_at.isoformat() if memory.deleted_at else None,
        )


class MemorySummaryResponse(BaseModel):
    """API DTO representing a lightweight Memory summary record."""

    memory_id: UUID = Field(description="Unique memory identifier")
    owner_id: str = Field(description="Owner identity identifier")
    type: str = Field(description="Memory category string")
    text_snippet: str = Field(description="Truncated text snippet")
    status: str = Field(description="Lifecycle status string")
    importance: str = Field(description="Importance rating string")
    confidence: str = Field(description="Confidence rating string")
    source: str = Field(description="Source origin indicator")
    created_at: str = Field(description="Creation UTC ISO timestamp")
    updated_at: str = Field(description="Update UTC ISO timestamp")
    last_accessed_at: str | None = Field(default=None, description="Last access UTC ISO timestamp")
    expires_at: str | None = Field(default=None, description="Expiration UTC ISO timestamp")
    tags: list[str] = Field(description="Indexing tags")

    @classmethod
    def from_domain(cls, summary: MemorySummary) -> "MemorySummaryResponse":
        """Construct DTO from domain summary model."""
        return cls(
            memory_id=summary.memory_id,
            owner_id=summary.owner_id,
            type=summary.type.value,
            text_snippet=summary.text_snippet,
            status=summary.status.value,
            importance=summary.importance.value,
            confidence=summary.confidence.value,
            source=summary.source.value,
            created_at=summary.created_at.isoformat(),
            updated_at=summary.updated_at.isoformat(),
            last_accessed_at=summary.last_accessed_at.isoformat()
            if summary.last_accessed_at
            else None,
            expires_at=summary.expires_at.isoformat() if summary.expires_at else None,
            tags=summary.tags,
        )


class MemoryListResponse(BaseModel):
    """Paginated memory list response wrapper."""

    memories: list[MemorySummaryResponse] = Field(description="List of memory summary records")
    total: int = Field(description="Total matching count")
    limit: int = Field(description="Page size limit")
    offset: int = Field(description="Page index offset")
    has_more: bool = Field(description="Flag indicating additional records exist")


class DuplicateCheckResponse(BaseModel):
    """API DTO output from duplicate memory check."""

    is_duplicate: bool = Field(description="Flag indicating if candidate is duplicate")
    existing_memory_id: UUID | None = Field(
        default=None, description="Existing memory ID if duplicate"
    )
    similarity_score: float = Field(description="Deterministic similarity score")
    match_type: str = Field(description="Match mechanism ('exact_hash', 'text_overlap', 'none')")

    @classmethod
    def from_domain(cls, result: MemoryDuplicateResult) -> "DuplicateCheckResponse":
        """Construct DTO from domain duplicate result."""
        return cls(
            is_duplicate=result.is_duplicate,
            existing_memory_id=result.existing_memory_id,
            similarity_score=result.similarity_score,
            match_type=result.match_type,
        )
