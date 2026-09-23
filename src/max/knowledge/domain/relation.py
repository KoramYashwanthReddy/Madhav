"""Domain model for Knowledge Relation."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from max.knowledge.domain.enums import (
    KnowledgeConfidence,
    KnowledgeRelationType,
    KnowledgeSourceType,
    KnowledgeStatus,
)
from max.knowledge.domain.metadata import KnowledgeMetadata


class KnowledgeRelation(BaseModel):
    """Directed relationship link between two Knowledge Entities."""

    id: str = Field(default_factory=lambda: f"rel_{uuid4().hex[:12]}")
    owner_id: str = Field(..., description="Owner user identifier")
    source_entity_id: str = Field(..., description="Origin entity ID")
    relation_type: KnowledgeRelationType = Field(..., description="Relationship category type")
    target_entity_id: str = Field(..., description="Destination target entity ID")
    confidence: KnowledgeConfidence = Field(
        default=KnowledgeConfidence.HIGH, description="Confidence rating"
    )
    source_type: KnowledgeSourceType = Field(
        default=KnowledgeSourceType.USER_EXPLICIT, description="Provenance source type"
    )
    source_reference: dict[str, Any] | None = Field(
        default=None, description="Source provenance metadata"
    )
    metadata: KnowledgeMetadata = Field(
        default_factory=KnowledgeMetadata, description="Extensible metadata"
    )
    status: KnowledgeStatus = Field(default=KnowledgeStatus.ACTIVE, description="Lifecycle status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    archived_at: datetime | None = Field(default=None, description="Archival timestamp")
    deleted_at: datetime | None = Field(default=None, description="Soft deletion timestamp")

    @model_validator(mode="after")
    def validate_endpoints(self) -> "KnowledgeRelation":
        s = self.source_entity_id.strip()
        t = self.target_entity_id.strip()
        o = self.owner_id.strip()
        if not s or not t or not o:
            raise ValueError("source_entity_id, target_entity_id, and owner_id cannot be empty")
        if s == t:
            raise ValueError("source_entity_id and target_entity_id cannot be identical")

        return self

    @property
    def is_active(self) -> bool:
        """Return True if relation is ACTIVE and not soft deleted."""
        return self.status == KnowledgeStatus.ACTIVE and self.deleted_at is None
