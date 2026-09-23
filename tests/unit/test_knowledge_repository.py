"""Unit tests for InMemoryKnowledgeRepository operations."""

from datetime import UTC, datetime

import pytest

from madhav.knowledge.domain.collection import KnowledgeCollection
from madhav.knowledge.domain.entity import KnowledgeEntity
from madhav.knowledge.domain.enums import (
    KnowledgeEntityType,
    KnowledgeRelationType,
    KnowledgeStatus,
)
from madhav.knowledge.domain.fact import KnowledgeFact
from madhav.knowledge.domain.filter import KnowledgeSearchFilter
from madhav.knowledge.domain.relation import KnowledgeRelation
from madhav.knowledge.domain.version import KnowledgeVersion
from madhav.knowledge.repositories.memory import InMemoryKnowledgeRepository


@pytest.mark.asyncio
async def test_repository_entity_lifecycle() -> None:
    repo = InMemoryKnowledgeRepository()
    now = datetime.now(UTC)

    entity = KnowledgeEntity(
        owner_id="user_1",
        type=KnowledgeEntityType.SKILL,
        name="Python",
        created_at=now,
        updated_at=now,
    )
    saved = await repo.create_entity(entity)
    assert saved.id == entity.id

    fetched = await repo.get_entity(entity.id)
    assert fetched is not None
    assert fetched.name == "Python"

    # Search entity
    spec = KnowledgeSearchFilter(owner_id="user_1", query="py")
    results, total = await repo.search_entities(spec)
    assert total == 1
    assert results[0].id == entity.id

    # Archive entity
    archived = await repo.archive_entity(entity.id, archived_at=now)
    assert archived.status == KnowledgeStatus.ARCHIVED

    # Restore entity
    restored = await repo.restore_entity(entity.id, updated_at=now)
    assert restored.status == KnowledgeStatus.ACTIVE

    # Soft Delete entity
    deleted = await repo.delete_entity(entity.id, soft_delete=True, deleted_at=now)
    assert deleted is True
    assert await repo.get_entity(entity.id) is None


@pytest.mark.asyncio
async def test_repository_fact_and_relation_operations() -> None:
    repo = InMemoryKnowledgeRepository()
    now = datetime.now(UTC)

    e1 = await repo.create_entity(
        KnowledgeEntity(
            owner_id="user_1",
            type=KnowledgeEntityType.PERSON,
            name="Alice",
            created_at=now,
            updated_at=now,
        )
    )
    e2 = await repo.create_entity(
        KnowledgeEntity(
            owner_id="user_1",
            type=KnowledgeEntityType.PROJECT,
            name="Madhav",
            created_at=now,
            updated_at=now,
        )
    )

    fact = await repo.create_fact(
        KnowledgeFact(
            owner_id="user_1",
            entity_id=e1.id,
            subject="Alice",
            predicate="role",
            object="Lead Architect",
            value="Lead Architect",
            created_at=now,
            updated_at=now,
        )
    )
    assert fact.id.startswith("fact_")

    facts = await repo.list_facts_by_entity(e1.id)
    assert len(facts) == 1
    assert facts[0].value == "Lead Architect"

    rel = await repo.create_relation(
        KnowledgeRelation(
            owner_id="user_1",
            source_entity_id=e1.id,
            relation_type=KnowledgeRelationType.WORKS_ON,
            target_entity_id=e2.id,
            created_at=now,
            updated_at=now,
        )
    )
    assert rel.id.startswith("rel_")

    out_rels = await repo.list_outgoing_relations(e1.id)
    assert len(out_rels) == 1
    assert out_rels[0].target_entity_id == e2.id

    inc_rels = await repo.list_incoming_relations(e2.id)
    assert len(inc_rels) == 1
    assert inc_rels[0].source_entity_id == e1.id


@pytest.mark.asyncio
async def test_repository_collection_and_versioning() -> None:
    repo = InMemoryKnowledgeRepository()
    now = datetime.now(UTC)

    col = await repo.create_collection(
        KnowledgeCollection(
            owner_id="user_1",
            name="Technology",
            created_at=now,
            updated_at=now,
        )
    )
    assert col.id.startswith("col_")

    cols, total = await repo.list_collections(owner_id="user_1")
    assert total == 1
    assert cols[0].name == "Technology"

    await repo.create_version(
        KnowledgeVersion(
            target_id="ent_100",
            target_type="entity",
            version_number=1,
            snapshot={"name": "v1"},
            changed_at=now,
        )
    )
    await repo.create_version(
        KnowledgeVersion(
            target_id="ent_100",
            target_type="entity",
            version_number=2,
            snapshot={"name": "v2"},
            changed_at=now,
        )
    )

    versions = await repo.list_versions("ent_100")
    assert len(versions) == 2
    latest = await repo.get_latest_version("ent_100")
    assert latest is not None
    assert latest.version_number == 2
