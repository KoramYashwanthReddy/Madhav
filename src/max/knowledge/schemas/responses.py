"""API response DTO models for Personal Knowledge Engine endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.knowledge.domain.collection import KnowledgeCollection
from max.knowledge.domain.entity import KnowledgeEntity
from max.knowledge.domain.enums import (
    FactValueType,
    KnowledgeConfidence,
    KnowledgeEntityType,
    KnowledgeRelationType,
    KnowledgeScope,
    KnowledgeSourceType,
    KnowledgeStatus,
)
from max.knowledge.domain.fact import KnowledgeFact
from max.knowledge.domain.metadata import KnowledgeMetadata
from max.knowledge.domain.relation import KnowledgeRelation


class KnowledgeEntityResponse(BaseModel):
    """API response model for a Knowledge Entity."""

    id: str
    owner_id: str
    type: KnowledgeEntityType
    name: str
    description: str | None
    status: KnowledgeStatus
    confidence: KnowledgeConfidence
    scope: KnowledgeScope
    collection_id: str | None
    metadata: KnowledgeMetadata
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    deleted_at: datetime | None

    @classmethod
    def from_domain(cls, entity: KnowledgeEntity) -> "KnowledgeEntityResponse":
        return cls(
            id=entity.id,
            owner_id=entity.owner_id,
            type=entity.type,
            name=entity.name,
            description=entity.description,
            status=entity.status,
            confidence=entity.confidence,
            scope=entity.scope,
            collection_id=entity.collection_id,
            metadata=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            archived_at=entity.archived_at,
            deleted_at=entity.deleted_at,
        )


class KnowledgeFactResponse(BaseModel):
    """API response model for a Knowledge Fact."""

    id: str
    owner_id: str
    entity_id: str
    subject: str
    predicate: str
    object: str
    value: Any
    value_type: FactValueType
    confidence: KnowledgeConfidence
    source_type: KnowledgeSourceType
    source_reference: dict[str, Any] | None
    status: KnowledgeStatus
    valid_from: datetime | None
    valid_until: datetime | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    deleted_at: datetime | None

    @classmethod
    def from_domain(cls, fact: KnowledgeFact) -> "KnowledgeFactResponse":
        return cls(
            id=fact.id,
            owner_id=fact.owner_id,
            entity_id=fact.entity_id,
            subject=fact.subject,
            predicate=fact.predicate,
            object=fact.object,
            value=fact.value,
            value_type=fact.value_type,
            confidence=fact.confidence,
            source_type=fact.source_type,
            source_reference=fact.source_reference,
            status=fact.status,
            valid_from=fact.valid_from,
            valid_until=fact.valid_until,
            created_at=fact.created_at,
            updated_at=fact.updated_at,
            archived_at=fact.archived_at,
            deleted_at=fact.deleted_at,
        )


class KnowledgeRelationResponse(BaseModel):
    """API response model for a Knowledge Relation."""

    id: str
    owner_id: str
    source_entity_id: str
    relation_type: KnowledgeRelationType
    target_entity_id: str
    confidence: KnowledgeConfidence
    source_type: KnowledgeSourceType
    source_reference: dict[str, Any] | None
    metadata: KnowledgeMetadata
    status: KnowledgeStatus
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    deleted_at: datetime | None

    @classmethod
    def from_domain(cls, relation: KnowledgeRelation) -> "KnowledgeRelationResponse":
        return cls(
            id=relation.id,
            owner_id=relation.owner_id,
            source_entity_id=relation.source_entity_id,
            relation_type=relation.relation_type,
            target_entity_id=relation.target_entity_id,
            confidence=relation.confidence,
            source_type=relation.source_type,
            source_reference=relation.source_reference,
            metadata=relation.metadata,
            status=relation.status,
            created_at=relation.created_at,
            updated_at=relation.updated_at,
            archived_at=relation.archived_at,
            deleted_at=relation.deleted_at,
        )


class KnowledgeCollectionResponse(BaseModel):
    """API response model for a Knowledge Collection."""

    id: str
    owner_id: str
    name: str
    description: str | None
    metadata: KnowledgeMetadata
    status: KnowledgeStatus
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    deleted_at: datetime | None

    @classmethod
    def from_domain(cls, col: KnowledgeCollection) -> "KnowledgeCollectionResponse":
        return cls(
            id=col.id,
            owner_id=col.owner_id,
            name=col.name,
            description=col.description,
            metadata=col.metadata,
            status=col.status,
            created_at=col.created_at,
            updated_at=col.updated_at,
            archived_at=col.archived_at,
            deleted_at=col.deleted_at,
        )


class KnowledgeSummaryResponse(BaseModel):
    """API response model for Knowledge Entity Summary projection."""

    entity: KnowledgeEntityResponse
    facts: list[KnowledgeFactResponse]
    outgoing_relations: list[KnowledgeRelationResponse]
    incoming_relations: list[KnowledgeRelationResponse]
    collection: KnowledgeCollectionResponse | None
    version_count: int


class KnowledgeListResponse[T](BaseModel):
    """Generic paginated envelope response for knowledge collections."""

    items: list[T] = Field(..., description="Page items")
    total: int = Field(..., description="Total available records count")
    page: int = Field(..., description="Current page index")
    page_size: int = Field(..., description="Page size limit")

