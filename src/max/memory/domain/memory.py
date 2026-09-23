"""Memory aggregate root domain model."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from max.memory.domain.content import MemoryContent
from max.memory.domain.enums import (
    MemoryConfidence,
    MemoryImportance,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
)
from max.memory.domain.metadata import MemoryMetadata


class Memory(BaseModel):
    """Domain aggregate root representing a persistent memory record."""

    memory_id: UUID = Field(default_factory=uuid4, description="Unique memory identifier")
    owner_id: str = Field(description="Owner identity identifier")
    type: MemoryType = Field(default=MemoryType.FACT, description="Memory classification category")
    content: MemoryContent = Field(description="Textual and structured memory content")
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE, description="Lifecycle status")
    importance: MemoryImportance = Field(
        default=MemoryImportance.NORMAL, description="Importance level rating"
    )
    confidence: MemoryConfidence = Field(
        default=MemoryConfidence.MEDIUM, description="Confidence rating"
    )
    source: MemorySource = Field(
        default=MemorySource.USER_EXPLICIT, description="Memory source origin"
    )
    scope: MemoryScope = Field(default=MemoryScope.USER, description="Memory scope/ownership level")
    metadata: MemoryMetadata = Field(
        default_factory=MemoryMetadata, description="Extensible metadata attributes"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation UTC ISO timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update UTC ISO timestamp",
    )
    last_accessed_at: datetime | None = Field(
        default=None, description="UTC ISO timestamp of last retrieval/access"
    )
    expires_at: datetime | None = Field(
        default=None, description="Optional expiration UTC ISO timestamp"
    )
    archived_at: datetime | None = Field(
        default=None, description="UTC ISO timestamp when record was archived"
    )
    deleted_at: datetime | None = Field(
        default=None, description="UTC ISO timestamp when record was soft deleted"
    )

    def is_active(self) -> bool:
        """Check if memory record is currently in ACTIVE status."""
        return self.status == MemoryStatus.ACTIVE

    def is_archived(self) -> bool:
        """Check if memory record is currently in ARCHIVED status."""
        return self.status == MemoryStatus.ARCHIVED

    def is_deleted(self) -> bool:
        """Check if memory record is currently in DELETED status."""
        return self.status == MemoryStatus.DELETED

    def is_expired(self, current_time: datetime | None = None) -> bool:
        """Check if memory record has passed its expiration timestamp."""
        if self.status == MemoryStatus.EXPIRED:
            return True
        if self.expires_at is None:
            return False
        now = current_time or datetime.now(UTC)
        return now >= self.expires_at
