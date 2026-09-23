"""Domain model for Knowledge Version history."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from madhav.knowledge.domain.enums import KnowledgeSourceType


class KnowledgeVersion(BaseModel):
    """Immutable historic snapshot tracking mutations to entities, facts, or relations."""

    version_id: str = Field(default_factory=lambda: f"ver_{uuid4().hex[:12]}")
    target_id: str = Field(..., description="Target object identifier")
    target_type: str = Field(..., description="Target object category ('entity', 'fact')")
    version_number: int = Field(..., description="Monotonically increasing version counter")
    snapshot: dict[str, Any] = Field(..., description="Serialized state dictionary of the object")
    changed_at: datetime = Field(..., description="Timestamp of change event")
    changed_by_source: KnowledgeSourceType = Field(
        default=KnowledgeSourceType.USER_EXPLICIT, description="Provenance source"
    )
    change_reason: str | None = Field(default=None, description="Optional change rationale")


    @field_validator("version_number")
    @classmethod
    def validate_version_number(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Version number must be >= 1")
        return v
