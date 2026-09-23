"""Memory duplicate detection result model."""

from uuid import UUID

from pydantic import BaseModel, Field


class MemoryDuplicateResult(BaseModel):
    """Output from deterministic duplicate memory detection check."""

    is_duplicate: bool = Field(description="Indicates whether candidate is a duplicate memory")
    existing_memory_id: UUID | None = Field(
        default=None, description="ID of existing matching memory if duplicate detected"
    )
    similarity_score: float = Field(
        default=0.0, description="Deterministic similarity score (0.0 to 1.0)"
    )
    match_type: str = Field(
        default="none", description="Match mechanism ('exact_hash', 'text_overlap', 'none')"
    )
