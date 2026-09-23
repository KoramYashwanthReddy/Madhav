"""Unit tests for Personal Knowledge Engine domain models and validations."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from max.knowledge.domain.collection import KnowledgeCollection
from max.knowledge.domain.entity import KnowledgeEntity
from max.knowledge.domain.enums import (
    FactValueType,
    KnowledgeConfidence,
    KnowledgeEntityType,
    KnowledgeRelationType,
    KnowledgeSourceType,
)
from max.knowledge.domain.fact import KnowledgeFact
from max.knowledge.domain.relation import KnowledgeRelation
from max.knowledge.domain.version import KnowledgeVersion


def test_entity_domain_creation_and_validation() -> None:
    now = datetime.now(UTC)
    entity = KnowledgeEntity(
        owner_id="user_123",
        type=KnowledgeEntityType.PROJECT,
        name="Max",
        description="Modular Personal AI Runtime",
        confidence=KnowledgeConfidence.HIGH,
        created_at=now,
        updated_at=now,
    )
    assert entity.id.startswith("ent_")
    assert entity.name == "Max"
    assert entity.type == KnowledgeEntityType.PROJECT
    assert entity.is_active is True

    # Empty name should raise ValueError/ValidationError
    with pytest.raises(ValidationError):
        KnowledgeEntity(
            owner_id="user_123",
            type=KnowledgeEntityType.PROJECT,
            name="   ",
            created_at=now,
            updated_at=now,
        )


def test_fact_domain_and_temporal_validity() -> None:
    now = datetime.now(UTC)
    fact = KnowledgeFact(
        owner_id="user_123",
        entity_id="ent_123",
        subject="user",
        predicate="learning",
        object="Spring Boot",
        value="Spring Boot 3",
        value_type=FactValueType.TEXT,
        confidence=KnowledgeConfidence.HIGH,
        source_type=KnowledgeSourceType.USER_EXPLICIT,
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=30),
        created_at=now,
        updated_at=now,
    )
    assert fact.is_active is True
    assert fact.is_valid_at(now) is True
    assert fact.is_valid_at(now - timedelta(days=2)) is False
    assert fact.is_valid_at(now + timedelta(days=40)) is False


def test_relation_domain_and_self_relation_validation() -> None:
    now = datetime.now(UTC)
    relation = KnowledgeRelation(
        owner_id="user_123",
        source_entity_id="ent_1",
        relation_type=KnowledgeRelationType.USES,
        target_entity_id="ent_2",
        created_at=now,
        updated_at=now,
    )
    assert relation.id.startswith("rel_")
    assert relation.is_active is True

    # Identical source and target should fail validation
    with pytest.raises(ValidationError):
        KnowledgeRelation(
            owner_id="user_123",
            source_entity_id="ent_1",
            relation_type=KnowledgeRelationType.USES,
            target_entity_id="ent_1",
            created_at=now,
            updated_at=now,
        )


def test_collection_domain() -> None:
    now = datetime.now(UTC)
    collection = KnowledgeCollection(
        owner_id="user_123",
        name="Projects",
        description="Active software projects",
        created_at=now,
        updated_at=now,
    )
    assert collection.id.startswith("col_")
    assert collection.name == "Projects"
    assert collection.is_active is True


def test_version_domain() -> None:
    now = datetime.now(UTC)
    version = KnowledgeVersion(
        target_id="ent_123",
        target_type="entity",
        version_number=1,
        snapshot={"name": "Max"},
        changed_at=now,
    )
    assert version.version_id.startswith("ver_")
    assert version.version_number == 1
