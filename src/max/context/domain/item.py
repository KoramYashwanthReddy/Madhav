"""ContextItem domain model representing a discrete unit of contextual information."""

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from max.context.domain.enums import ContextCategory, ContextPriority, SourceTrustLevel


class ContextItem(BaseModel):
    """Normalized, provider-neutral representation of a candidate context unit."""

    context_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for context item",
    )
    category: ContextCategory = Field(
        default=ContextCategory.OTHER, description="Context category taxonomy"
    )
    content: str = Field(description="Raw text content of the context item")
    priority: ContextPriority = Field(
        default=ContextPriority.NORMAL, description="Item priority for budget allocation"
    )
    required: bool = Field(
        default=False, description="Mandatory flag preventing dropping unless budget impossible"
    )
    source: str = Field(
        default="unknown", description="Identifier of context source supplying this item"
    )
    token_estimate: int = Field(
        default=0, description="Estimated token count consumed by this item", ge=0
    )
    trust_level: SourceTrustLevel = Field(
        default=SourceTrustLevel.NORMAL, description="Security trust level of item source"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary safe metadata key-value pairs"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Item creation UTC timestamp",
    )
    expires_at: datetime | None = Field(
        default=None, description="Optional expiration UTC timestamp"
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure context item text is non-empty and stripped of outer whitespace."""
        if not v or not v.strip():
            raise ValueError("ContextItem content cannot be empty or whitespace-only.")
        return v.strip()

    @property
    def content_hash(self) -> str:
        """Generate a deterministic SHA-256 hash of normalized item content for deduplication."""
        normalized = " ".join(self.content.split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @property
    def is_expired(self) -> bool:
        """Check whether context item has passed its expiration timestamp."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at
