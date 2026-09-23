"""Domain model for deterministic Knowledge Search filter specifications."""

from pydantic import BaseModel, Field

from madhav.knowledge.domain.enums import (
    KnowledgeConfidence,
    KnowledgeEntityType,
    KnowledgeSourceType,
    KnowledgeStatus,
)


class KnowledgeSearchFilter(BaseModel):
    """Query parameter specification for deterministic knowledge search."""

    owner_id: str | None = Field(default=None, description="Optional owner filter boundary")
    query: str | None = Field(
        default=None, description="Case-insensitive substring search for name and description"
    )
    entity_type: KnowledgeEntityType | None = Field(
        default=None, description="Optional entity type filter"
    )
    status: KnowledgeStatus | None = Field(
        default=KnowledgeStatus.ACTIVE, description="Lifecycle status filter"
    )
    confidence: KnowledgeConfidence | None = Field(
        default=None, description="Optional confidence rating filter"
    )
    collection_id: str | None = Field(
        default=None, description="Optional collection binding filter"
    )
    tags: list[str] | None = Field(
        default=None, description="Optional tags match filter (matches if any tag present)"
    )
    source_type: KnowledgeSourceType | None = Field(
        default=None, description="Optional provenance source type filter"
    )
    page: int = Field(default=1, ge=1, description="Pagination page index (1-based)")
    page_size: int = Field(default=50, ge=1, le=200, description="Pagination page size limit")
