"""Unit tests for KnowledgeService business logic."""

from datetime import UTC, datetime

import pytest

from max.common.clock import DeterministicClock
from max.knowledge.domain.enums import (
    FactValueType,
    KnowledgeEntityType,
    KnowledgeRelationType,
)
from max.knowledge.exceptions import (
    DuplicateKnowledgeError,
    InvalidFactValueError,
    InvalidKnowledgeRelationError,
    KnowledgeOwnershipError,
)
from max.knowledge.repositories.memory import InMemoryKnowledgeRepository
from max.knowledge.services.knowledge_service import KnowledgeService


@pytest.fixture
def service() -> KnowledgeService:
    repo = InMemoryKnowledgeRepository()
    clock = DeterministicClock(datetime(2026, 9, 24, 12, 0, 0, tzinfo=UTC))
    return KnowledgeService(
        entity_repo=repo,
        fact_repo=repo,
        relation_repo=repo,
        collection_repo=repo,
        version_repo=repo,
        clock=clock,
        duplicate_detection_enabled=True,
    )


@pytest.mark.asyncio
async def test_create_and_get_entity(service: KnowledgeService) -> None:
    entity = await service.create_entity(
        owner_id="user_1",
        type=KnowledgeEntityType.SKILL,
        name="Java",
        description="Java 21 Development",
    )
    assert entity.id.startswith("ent_")
    assert entity.name == "Java"

    fetched = await service.get_entity(entity.id, owner_id="user_1")
    assert fetched.name == "Java"

    # Mismatched owner raises KnowledgeOwnershipError
    with pytest.raises(KnowledgeOwnershipError):
        await service.get_entity(entity.id, owner_id="other_user")


@pytest.mark.asyncio
async def test_duplicate_entity_detection(service: KnowledgeService) -> None:
    await service.create_entity(
        owner_id="user_1",
        type=KnowledgeEntityType.SKILL,
        name="Java",
    )
    # Creating exact duplicate (same owner, type, normalized name) raises DuplicateKnowledgeError
    with pytest.raises(DuplicateKnowledgeError):
        await service.create_entity(
            owner_id="user_1",
            type=KnowledgeEntityType.SKILL,
            name="java  ",
        )

    # Creating with allow_duplicate=True succeeds
    dup = await service.create_entity(
        owner_id="user_1",
        type=KnowledgeEntityType.SKILL,
        name="java",
        allow_duplicate=True,
    )
    assert dup.id is not None


@pytest.mark.asyncio
async def test_fact_creation_and_value_validation(service: KnowledgeService) -> None:
    ent = await service.create_entity(
        owner_id="user_1",
        type=KnowledgeEntityType.PROJECT,
        name="Max",
    )
    fact = await service.create_fact(
        owner_id="user_1",
        entity_id=ent.id,
        subject="Max",
        predicate="uses_language",
        object="Python",
        value="Python 3.12",
        value_type=FactValueType.TEXT,
    )
    assert fact.id.startswith("fact_")

    # Invalid fact value type validation
    with pytest.raises(InvalidFactValueError):
        await service.create_fact(
            owner_id="user_1",
            entity_id=ent.id,
            subject="Max",
            predicate="version",
            object="1.0",
            value="not_a_number",
            value_type=FactValueType.NUMBER,
        )


@pytest.mark.asyncio
async def test_relation_creation_and_traversal(service: KnowledgeService) -> None:
    e1 = await service.create_entity(
        owner_id="user_1",
        type=KnowledgeEntityType.PERSON,
        name="Max User",
    )
    e2 = await service.create_entity(
        owner_id="user_1",
        type=KnowledgeEntityType.PROJECT,
        name="Max Engine",
    )
    rel = await service.create_relation(
        owner_id="user_1",
        source_entity_id=e1.id,
        relation_type=KnowledgeRelationType.OWNS,
        target_entity_id=e2.id,
    )
    assert rel.id.startswith("rel_")

    # Self-relation error
    with pytest.raises(InvalidKnowledgeRelationError):
        await service.create_relation(
            owner_id="user_1",
            source_entity_id=e1.id,
            relation_type=KnowledgeRelationType.OWNS,
            target_entity_id=e1.id,
        )


@pytest.mark.asyncio
async def test_knowledge_summary_projection(service: KnowledgeService) -> None:
    e1 = await service.create_entity(
        owner_id="user_1",
        type=KnowledgeEntityType.PROJECT,
        name="Max App",
    )
    await service.create_fact(
        owner_id="user_1",
        entity_id=e1.id,
        subject="Max App",
        predicate="status",
        object="Active Development",
        value="Active Development",
    )

    summary = await service.get_knowledge_summary(e1.id, owner_id="user_1")
    assert summary.entity.id == e1.id
    assert len(summary.facts) == 1
    assert summary.facts[0].predicate == "status"
