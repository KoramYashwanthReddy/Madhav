"""Memory summary projection model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from max.memory.domain.enums import (
    MemoryConfidence,
    MemoryImportance,
    MemorySource,
    MemoryStatus,
    MemoryType,
)
from max.memory.domain.memory import Memory


class MemorySummary(BaseModel):
    """Lightweight projection of a Memory object without detailed structured payload."""

    memory_id: UUID = Field(description="Unique memory identifier")
    owner_id: str = Field(description="Owner identity identifier")
    type: MemoryType = Field(description="Memory classification category")
    text_snippet: str = Field(description="Truncated safe text snippet")
    status: MemoryStatus = Field(description="Lifecycle status")
    importance: MemoryImportance = Field(description="Importance rating")
    confidence: MemoryConfidence = Field(description="Confidence rating")
    source: MemorySource = Field(description="Source origin")
    created_at: datetime = Field(description="Creation UTC ISO timestamp")
    updated_at: datetime = Field(description="Update UTC ISO timestamp")
    last_accessed_at: datetime | None = Field(default=None, description="Last access timestamp")
    expires_at: datetime | None = Field(default=None, description="Expiration timestamp")
    tags: list[str] = Field(default_factory=list, description="Associated safe indexing tags")

    @classmethod
    def from_memory(cls, memory: Memory, snippet_length: int = 100) -> "MemorySummary":
        """Construct a MemorySummary from a full Memory aggregate."""
        raw_text = memory.content.text
        snippet = raw_text[:snippet_length] + "..." if len(raw_text) > snippet_length else raw_text
        return cls(
            memory_id=memory.memory_id,
            owner_id=memory.owner_id,
            type=memory.type,
            text_snippet=snippet,
            status=memory.status,
            importance=memory.importance,
            confidence=memory.confidence,
            source=memory.source,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            last_accessed_at=memory.last_accessed_at,
            expires_at=memory.expires_at,
            tags=memory.metadata.tags,
        )
