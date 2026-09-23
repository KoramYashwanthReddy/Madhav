"""Domain model for extensible Knowledge Metadata."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeMetadata(BaseModel):
    """Safe extensible metadata container for knowledge entities, facts, and relations."""

    model_config = ConfigDict(frozen=True)

    tags: list[str] = Field(default_factory=list, description="Tag labels for categorization")
    external_reference: str | None = Field(
        default=None, description="Optional external resource identifier or URL string"
    )
    source_reference: dict[str, Any] | None = Field(
        default=None,
        description="Structured provenance details (e.g. memory_id, conversation_id, message_id)",
    )
    custom_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary safe non-secret custom key-value pairs"
    )
