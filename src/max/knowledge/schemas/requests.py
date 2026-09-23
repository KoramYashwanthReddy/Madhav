"""API request DTO models for Personal Knowledge Engine endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from max.knowledge.domain.enums import (
    FactValueType,
    KnowledgeConfidence,
    KnowledgeEntityType,
    KnowledgeRelationType,
    KnowledgeScope,
    KnowledgeSourceType,
    KnowledgeStatus,
)


class CreateEntityRequest(BaseModel):
    """API payload for creating a Knowledge Entity."""

    type: KnowledgeEntityType = Field(..., description="Entity category type")
    name: str = Field(..., description="Canonical name")
    description: str | None = Field(default=None, description="Optional description")
    confidence: KnowledgeConfidence = Field(
        default=KnowledgeConfidence.HIGH, description="Confidence rating"
    )
    scope: KnowledgeScope = Field(default=KnowledgeScope.USER, description="Scope boundary")
    collection_id: str | None = Field(default=None, description="Optional collection binding")
    tags: list[str] = Field(default_factory=list, description="Metadata tags")
    external_reference: str | None = Field(default=None, description="External reference URL/ID")
    source_reference: dict[str, Any] | None = Field(
        default=None, description="Structured provenance details"
    )
    custom_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata pairs"
    )
    allow_duplicate: bool = Field(
        default=False, description="Bypass duplicate entity check if True"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Entity name cannot be empty")
        return s


class UpdateEntityRequest(BaseModel):
    """API payload for updating a Knowledge Entity."""

    name: str | None = Field(default=None, description="Updated name")
    description: str | None = Field(default=None, description="Updated description")
    confidence: KnowledgeConfidence | None = Field(default=None, description="Updated confidence")
    collection_id: str | None = Field(default=None, description="Updated collection binding")
    tags: list[str] | None = Field(default=None, description="Updated metadata tags")
    external_reference: str | None = Field(default=None, description="Updated external reference")
    custom_metadata: dict[str, Any] | None = Field(
        default=None, description="Updated custom metadata"
    )
    change_reason: str | None = Field(default=None, description="Rationale for modification")


class CreateFactRequest(BaseModel):
    """API payload for creating a Knowledge Fact."""

    entity_id: str = Field(..., description="Associated entity ID")
    subject: str = Field(..., description="Fact subject")
    predicate: str = Field(..., description="Fact predicate key")
    object: str = Field(..., description="Fact object target")
    value: Any = Field(..., description="Typed value representation")
    value_type: FactValueType = Field(default=FactValueType.TEXT, description="Declared value type")
    confidence: KnowledgeConfidence = Field(
        default=KnowledgeConfidence.HIGH, description="Confidence rating"
    )
    source_type: KnowledgeSourceType = Field(
        default=KnowledgeSourceType.USER_EXPLICIT, description="Provenance source category"
    )
    source_reference: dict[str, Any] | None = Field(
        default=None, description="Source provenance metadata"
    )
    valid_from: datetime | None = Field(default=None, description="Validity start timestamp")
    valid_until: datetime | None = Field(default=None, description="Validity end timestamp")
    allow_duplicate: bool = Field(default=False, description="Bypass duplicate check if True")


class UpdateFactRequest(BaseModel):
    """API payload for updating a Knowledge Fact."""

    subject: str | None = Field(default=None, description="Updated subject")
    predicate: str | None = Field(default=None, description="Updated predicate")
    object: str | None = Field(default=None, description="Updated object")
    value: Any | None = Field(default=None, description="Updated value")
    value_type: FactValueType | None = Field(default=None, description="Updated value type")
    confidence: KnowledgeConfidence | None = Field(default=None, description="Updated confidence")
    valid_from: datetime | None = Field(default=None, description="Updated validity start")
    valid_until: datetime | None = Field(default=None, description="Updated validity end")
    change_reason: str | None = Field(default=None, description="Change rationale")


class CreateRelationRequest(BaseModel):
    """API payload for creating a Knowledge Relation."""

    source_entity_id: str = Field(..., description="Source entity ID")
    relation_type: KnowledgeRelationType = Field(..., description="Relationship category type")
    target_entity_id: str = Field(..., description="Target entity ID")
    confidence: KnowledgeConfidence = Field(
        default=KnowledgeConfidence.HIGH, description="Confidence rating"
    )
    source_type: KnowledgeSourceType = Field(
        default=KnowledgeSourceType.USER_EXPLICIT, description="Source category"
    )
    source_reference: dict[str, Any] | None = Field(
        default=None, description="Source provenance metadata"
    )
    tags: list[str] = Field(default_factory=list, description="Metadata tags")
    custom_metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class CreateCollectionRequest(BaseModel):
    """API payload for creating a Knowledge Collection."""

    name: str = Field(..., description="Collection display name")
    description: str | None = Field(default=None, description="Optional description")
    tags: list[str] = Field(default_factory=list, description="Metadata tags")
    custom_metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Collection name cannot be empty")
        return s


class UpdateCollectionRequest(BaseModel):
    """API payload for updating a Knowledge Collection."""

    name: str | None = Field(default=None, description="Updated collection name")
    description: str | None = Field(default=None, description="Updated collection description")
    tags: list[str] | None = Field(default=None, description="Updated tags")
    custom_metadata: dict[str, Any] | None = Field(
        default=None, description="Updated custom metadata"
    )



class KnowledgeSearchRequest(BaseModel):
    """API payload for deterministic Knowledge search."""

    query: str | None = Field(default=None, description="Substring search query")
    entity_type: KnowledgeEntityType | None = Field(default=None, description="Entity type filter")
    status: KnowledgeStatus | None = Field(
        default=KnowledgeStatus.ACTIVE, description="Lifecycle status filter"
    )
    confidence: KnowledgeConfidence | None = Field(default=None, description="Confidence filter")
    collection_id: str | None = Field(default=None, description="Collection binding filter")
    tags: list[str] | None = Field(default=None, description="Tags match filter")
    source_type: KnowledgeSourceType | None = Field(default=None, description="Source type filter")
    page: int = Field(default=1, ge=1, description="Page index (1-based)")
    page_size: int = Field(default=50, ge=1, le=200, description="Page size limit")
