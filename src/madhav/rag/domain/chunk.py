"""Document Chunk domain model for RAG & Retrieval Engine."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Domain model representing a single deterministic chunk of a Document."""

    chunk_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Chunk unique identifier"
    )
    document_id: str = Field(description="Parent Document identifier")
    owner_id: str = Field(description="Owner user identifier")
    chunk_index: int = Field(description="Zero-based sequence index within document")
    text: str = Field(description="Chunk text payload")
    character_start: int = Field(description="Starting character index in normalized document text")
    character_end: int = Field(description="Ending character index in normalized document text")
    token_estimate: int = Field(default=0, description="Estimated token count for chunk payload")
    metadata: dict[str, str | int | float | bool | list[str]] = Field(
        default_factory=dict, description="Metadata preserved from parent or chunking context"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Chunk creation timestamp"
    )
