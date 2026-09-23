"""Domain aggregate for Knowledge Entity."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from max.knowledge.domain.enums import (
    KnowledgeConfidence,
    KnowledgeEntityType,
    KnowledgeScope,
    KnowledgeStatus,
)
from max.knowledge.domain.metadata import KnowledgeMetadata


class KnowledgeEntity(BaseModel):
    """Aggregate root representing a persistent real-world or conceptual object."""

    id: str = Field(default_factory=lambda: f"ent_{uuid4().hex[:12]}")
    owner_id: str = Field(..., description="Owner user identifier")
    type: KnowledgeEntityType = Field(..., description="Entity category type")
    name: str = Field(..., description="Canonical entity name")
    description: str | None = Field(default=None, description="Optional detailed description")

    status: KnowledgeStatus = Field(default=KnowledgeStatus.ACTIVE, description="Lifecycle status")
    confidence: KnowledgeConfidence = Field(
        default=KnowledgeConfidence.HIGH, description="Provenance confidence level"
    )
    scope: KnowledgeScope = Field(default=KnowledgeScope.USER, description="Scope boundary")
    collection_id: str | None = Field(
        default=None, description="Optional associated knowledge collection ID"
    )
    metadata: KnowledgeMetadata = Field(
        default_factory=KnowledgeMetadata, description="Extensible metadata"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    archived_at: datetime | None = Field(default=None, description="Archival timestamp")
    deleted_at: datetime | None = Field(default=None, description="Soft deletion timestamp")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Knowledge entity name cannot be empty or whitespace only")
        return s

    @field_validator("owner_id")
    @classmethod
    def validate_owner_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Knowledge entity owner_id cannot be empty or whitespace only")
        return s

    @property
    def is_active(self) -> bool:
        """Return True if entity lifecycle status is ACTIVE."""
        return self.status == KnowledgeStatus.ACTIVE and self.deleted_at is None
