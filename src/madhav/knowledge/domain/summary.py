"""Domain model for Knowledge Summary projection."""

from pydantic import BaseModel, Field

from madhav.knowledge.domain.collection import KnowledgeCollection
from madhav.knowledge.domain.entity import KnowledgeEntity
from madhav.knowledge.domain.fact import KnowledgeFact
from madhav.knowledge.domain.relation import KnowledgeRelation


class KnowledgeSummary(BaseModel):
    """Safe aggregated summary view of an Entity and its associated facts and relations."""

    entity: KnowledgeEntity = Field(..., description="Root knowledge entity")
    facts: list[KnowledgeFact] = Field(
        default_factory=list, description="Active associated knowledge facts"
    )
    outgoing_relations: list[KnowledgeRelation] = Field(
        default_factory=list, description="Outgoing relationships originating from this entity"
    )
    incoming_relations: list[KnowledgeRelation] = Field(
        default_factory=list, description="Incoming relationships targeting this entity"
    )
    collection: KnowledgeCollection | None = Field(
        default=None, description="Associated collection if present"
    )
    version_count: int = Field(default=1, description="Total recorded version count")
