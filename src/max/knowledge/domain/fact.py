"""Domain model for Knowledge Fact."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from max.knowledge.domain.enums import (
    FactValueType,
    KnowledgeConfidence,
    KnowledgeSourceType,
    KnowledgeStatus,
)


class KnowledgeFact(BaseModel):
    """Statement assertion associated with a Knowledge Entity."""

    id: str = Field(default_factory=lambda: f"fact_{uuid4().hex[:12]}")
    owner_id: str = Field(..., description="Owner user identifier")
    entity_id: str = Field(..., description="Associated knowledge entity ID")
    subject: str = Field(..., description="Subject of the fact statement")
    predicate: str = Field(..., description="Predicate relationship or property key")
    object: str = Field(..., description="Object target or textual representation")
    value: Any = Field(..., description="Typed value representation of the fact assertion")
    value_type: FactValueType = Field(default=FactValueType.TEXT, description="Declared value type")
    confidence: KnowledgeConfidence = Field(
        default=KnowledgeConfidence.HIGH, description="Confidence rating"
    )
    source_type: KnowledgeSourceType = Field(
        default=KnowledgeSourceType.USER_EXPLICIT, description="Provenance source category"
    )
    source_reference: dict[str, Any] | None = Field(
        default=None, description="Source provenance details (e.g. memory_id, conversation_id)"
    )
    status: KnowledgeStatus = Field(default=KnowledgeStatus.ACTIVE, description="Lifecycle status")
    valid_from: datetime | None = Field(
        default=None, description="Optional temporal validity starting timestamp"
    )
    valid_until: datetime | None = Field(
        default=None, description="Optional temporal validity expiration timestamp"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    archived_at: datetime | None = Field(default=None, description="Archival timestamp")
    deleted_at: datetime | None = Field(default=None, description="Soft deletion timestamp")

    @field_validator("subject", "predicate", "object", "owner_id", "entity_id")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError(
                "Fact string fields (subject, predicate, object, owner_id) cannot be empty"
            )


        return s

    @property
    def is_active(self) -> bool:
        """Return True if fact status is ACTIVE and not soft-deleted."""
        return self.status == KnowledgeStatus.ACTIVE and self.deleted_at is None

    def is_valid_at(self, at_time: datetime) -> bool:
        """Return True if fact is temporally valid at specified timestamp."""
        if not self.is_active:
            return False
        if self.valid_from and at_time < self.valid_from:
            return False
        if self.valid_until and at_time > self.valid_until:
            return False
        return True
