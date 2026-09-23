"""Memory metadata domain model."""

from typing import Any

from pydantic import BaseModel, Field


class MemoryMetadata(BaseModel):
    """Extensible safe metadata attributes associated with a memory record."""

    source_reference: str | None = Field(
        default=None, description="Reference identifier of external source document or event"
    )
    conversation_id: str | None = Field(
        default=None, description="Origin conversation identifier if derived from chat"
    )
    message_id: str | None = Field(
        default=None, description="Origin message identifier if derived from chat"
    )
    tags: list[str] = Field(
        default_factory=list, description="Safe indexing tags for categorization and search"
    )
    origin: str | None = Field(default=None, description="Client or component origin string")
    created_by: str | None = Field(default=None, description="Identifier of creator entity")
    custom_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Safe arbitrary key-value metadata attributes"
    )
