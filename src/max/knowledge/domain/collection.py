"""Domain model for Knowledge Collection."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from max.knowledge.domain.enums import KnowledgeStatus
from max.knowledge.domain.metadata import KnowledgeMetadata


class KnowledgeCollection(BaseModel):
    """Organizational container grouping related Knowledge Entities."""

    id: str = Field(default_factory=lambda: f"col_{uuid4().hex[:12]}")
    owner_id: str = Field(..., description="Owner user identifier")
    name: str = Field(..., description="Collection display name")
    description: str | None = Field(default=None, description="Optional collection description")
    metadata: KnowledgeMetadata = Field(
        default_factory=KnowledgeMetadata, description="Extensible metadata"
    )
    status: KnowledgeStatus = Field(default=KnowledgeStatus.ACTIVE, description="Lifecycle status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    archived_at: datetime | None = Field(default=None, description="Archival timestamp")
    deleted_at: datetime | None = Field(default=None, description="Soft deletion timestamp")

    @field_validator("name", "owner_id")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Knowledge collection name and owner_id cannot be empty")
        return s

    @property
    def is_active(self) -> bool:
        """Return True if collection is ACTIVE and not soft deleted."""
        return self.status == KnowledgeStatus.ACTIVE and self.deleted_at is None
