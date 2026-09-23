"""Domain model for deterministic Knowledge Duplicate detection result."""

from pydantic import BaseModel, Field


class KnowledgeDuplicateResult(BaseModel):
    """Outcome payload of deterministic duplicate check."""

    is_duplicate: bool = Field(..., description="True if potential duplicate was detected")
    matched_entity_id: str | None = Field(
        default=None, description="Matched existing entity ID if duplicate entity detected"
    )
    matched_fact_id: str | None = Field(
        default=None, description="Matched existing fact ID if duplicate fact detected"
    )
    similarity_score: float = Field(
        default=1.0, description="Match score (1.0 for exact normalized deterministic match)"
    )
    reason: str | None = Field(default=None, description="Explanation of duplicate match criteria")
