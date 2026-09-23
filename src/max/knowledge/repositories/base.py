"""Abstract repository interfaces/protocols for Personal Knowledge Engine."""

from datetime import datetime
from typing import Protocol

from max.knowledge.domain.collection import KnowledgeCollection
from max.knowledge.domain.entity import KnowledgeEntity
from max.knowledge.domain.enums import (
    KnowledgeConfidence,
    KnowledgeRelationType,
    KnowledgeStatus,
)
from max.knowledge.domain.fact import KnowledgeFact
from max.knowledge.domain.filter import KnowledgeSearchFilter
from max.knowledge.domain.relation import KnowledgeRelation
from max.knowledge.domain.version import KnowledgeVersion


class KnowledgeEntityRepository(Protocol):
    """Repository interface for Knowledge Entities."""

    async def create_entity(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """Persist a new entity record."""
        ...

    async def get_entity(self, entity_id: str) -> KnowledgeEntity | None:
        """Retrieve entity by ID."""
        ...

    async def list_entities(
        self, filter_spec: KnowledgeSearchFilter
    ) -> tuple[list[KnowledgeEntity], int]:
        """List entities matching filter with pagination."""
        ...

    async def update_entity(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """Update existing entity record."""
        ...

    async def archive_entity(self, entity_id: str, archived_at: datetime) -> KnowledgeEntity:
        """Archive entity record."""
        ...

    async def restore_entity(self, entity_id: str, updated_at: datetime) -> KnowledgeEntity:
        """Restore entity record to active state."""
        ...

    async def delete_entity(
        self, entity_id: str, soft_delete: bool = True, deleted_at: datetime | None = None
    ) -> bool:
        """Delete entity record."""
        ...

    async def search_entities(
        self, filter_spec: KnowledgeSearchFilter
    ) -> tuple[list[KnowledgeEntity], int]:
        """Deterministic search across entities."""
        ...

    async def count_entities(
        self, owner_id: str, status: KnowledgeStatus | None = None
    ) -> int:
        """Count total matching entities for owner."""
        ...


class KnowledgeFactRepository(Protocol):
    """Repository interface for Knowledge Facts."""

    async def create_fact(self, fact: KnowledgeFact) -> KnowledgeFact:
        """Persist a new fact record."""
        ...

    async def get_fact(self, fact_id: str) -> KnowledgeFact | None:
        """Retrieve fact by ID."""
        ...

    async def list_facts_by_entity(
        self, entity_id: str, status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE
    ) -> list[KnowledgeFact]:
        """Retrieve facts belonging to specified entity."""
        ...

    async def list_facts(
        self,
        owner_id: str,
        predicate: str | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
        confidence: KnowledgeConfidence | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[KnowledgeFact], int]:
        """List facts for owner with optional predicate and status filters."""
        ...

    async def update_fact(self, fact: KnowledgeFact) -> KnowledgeFact:
        """Update existing fact record."""
        ...

    async def archive_fact(self, fact_id: str, archived_at: datetime) -> KnowledgeFact:
        """Archive fact record."""
        ...

    async def delete_fact(
        self, fact_id: str, soft_delete: bool = True, deleted_at: datetime | None = None
    ) -> bool:
        """Delete fact record."""
        ...


class KnowledgeRelationRepository(Protocol):
    """Repository interface for Knowledge Relations."""

    async def create_relation(self, relation: KnowledgeRelation) -> KnowledgeRelation:
        """Persist a new relation link."""
        ...

    async def get_relation(self, relation_id: str) -> KnowledgeRelation | None:
        """Retrieve relation by ID."""
        ...

    async def delete_relation(
        self, relation_id: str, soft_delete: bool = True, deleted_at: datetime | None = None
    ) -> bool:
        """Delete relation link."""
        ...

    async def list_outgoing_relations(
        self,
        entity_id: str,
        relation_type: KnowledgeRelationType | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        """List outgoing relations originating from entity."""
        ...

    async def list_incoming_relations(
        self,
        entity_id: str,
        relation_type: KnowledgeRelationType | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        """List incoming relations targeting entity."""
        ...

    async def find_relations_between(
        self,
        source_entity_id: str,
        target_entity_id: str,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        """List direct relations between source and target entities."""
        ...


class KnowledgeCollectionRepository(Protocol):
    """Repository interface for Knowledge Collections."""

    async def create_collection(self, collection: KnowledgeCollection) -> KnowledgeCollection:
        """Persist a new collection."""
        ...

    async def get_collection(self, collection_id: str) -> KnowledgeCollection | None:
        """Retrieve collection by ID."""
        ...

    async def update_collection(self, collection: KnowledgeCollection) -> KnowledgeCollection:
        """Update collection metadata/description."""
        ...

    async def list_collections(
        self,
        owner_id: str,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[KnowledgeCollection], int]:
        """List collections for owner."""
        ...

    async def archive_collection(
        self, collection_id: str, archived_at: datetime
    ) -> KnowledgeCollection:
        """Archive collection."""
        ...


    async def delete_collection(
        self, collection_id: str, soft_delete: bool = True, deleted_at: datetime | None = None
    ) -> bool:
        """Delete collection."""
        ...


class KnowledgeVersionRepository(Protocol):
    """Repository interface for Knowledge Version history."""

    async def create_version(self, version: KnowledgeVersion) -> KnowledgeVersion:
        """Persist a version record."""
        ...

    async def list_versions(self, target_id: str) -> list[KnowledgeVersion]:
        """Retrieve version history for target object."""
        ...

    async def get_latest_version(self, target_id: str) -> KnowledgeVersion | None:
        """Retrieve latest version record for target object."""
        ...
