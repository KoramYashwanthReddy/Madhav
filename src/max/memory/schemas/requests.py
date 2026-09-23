"""API request DTO models for Memory Engine endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from max.memory.domain.enums import (
    MemoryConfidence,
    MemoryImportance,
    MemorySource,
    MemoryStatus,
    MemoryType,
)


class CreateMemoryRequest(BaseModel):
    """API payload for explicit memory creation."""

    type: MemoryType = Field(default=MemoryType.FACT, description="Memory category type")
    text: str = Field(description="Primary memory text payload")
    structured_data: dict[str, Any] = Field(
        default_factory=dict, description="Optional key-value structured data"
    )
    importance: MemoryImportance = Field(
        default=MemoryImportance.NORMAL, description="Importance rating"
    )
    confidence: MemoryConfidence = Field(
        default=MemoryConfidence.MEDIUM, description="Confidence rating"
    )
    source: MemorySource = Field(
        default=MemorySource.USER_EXPLICIT, description="Source origin indicator"
    )
    tags: list[str] = Field(default_factory=list, description="Indexing tags")
    source_reference: str | None = Field(default=None, description="External document reference")
    conversation_id: str | None = Field(default=None, description="Origin conversation ID")
    message_id: str | None = Field(default=None, description="Origin message ID")
    custom_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Safe custom metadata"
    )
    expires_at: datetime | None = Field(default=None, description="Optional expiration timestamp")
    check_duplicate: bool = Field(
        default=True, description="Toggle duplicate detection check before creation"
    )

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text payload is non-empty and stripped of outer whitespace."""
        if not v or not v.strip():
            raise ValueError("Memory text content cannot be empty or whitespace-only.")
        return v.strip()


class UpdateMemoryRequest(BaseModel):
    """API payload for updating a memory record."""

    text: str | None = Field(default=None, description="Updated text content")
    structured_data: dict[str, Any] | None = Field(
        default=None, description="Updated structured data payload"
    )
    importance: MemoryImportance | None = Field(
        default=None, description="Updated importance level"
    )
    confidence: MemoryConfidence | None = Field(
        default=None, description="Updated confidence level"
    )
    tags: list[str] | None = Field(default=None, description="Updated indexing tags")
    custom_metadata: dict[str, Any] | None = Field(
        default=None, description="Updated custom metadata"
    )
    expires_at: datetime | None = Field(default=None, description="Updated expiration timestamp")


class MemorySearchRequest(BaseModel):
    """API payload for querying and searching memories."""

    query: str | None = Field(default=None, description="Substring search query")
    types: list[MemoryType] | None = Field(default=None, description="Filter by types")
    statuses: list[MemoryStatus] | None = Field(default=None, description="Filter by statuses")
    importances: list[MemoryImportance] | None = Field(
        default=None, description="Filter by importances"
    )
    sources: list[MemorySource] | None = Field(default=None, description="Filter by sources")
    tags: list[str] | None = Field(default=None, description="Filter by tags")
    include_expired: bool = Field(default=False, description="Include EXPIRED records")
    include_archived: bool = Field(default=False, description="Include ARCHIVED records")
    include_deleted: bool = Field(default=False, description="Include soft DELETED records")
    limit: int = Field(default=50, ge=1, le=200, description="Page size limit")
    offset: int = Field(default=0, ge=0, description="Page index offset")
