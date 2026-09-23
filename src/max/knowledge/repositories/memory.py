"""In-memory implementation of Personal Knowledge Engine repositories."""

import asyncio
from datetime import datetime

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
from max.knowledge.exceptions import (
    KnowledgeCollectionNotFoundError,
    KnowledgeEntityNotFoundError,
    KnowledgeFactNotFoundError,
)
from max.knowledge.repositories.base import (
    KnowledgeCollectionRepository,
    KnowledgeEntityRepository,
    KnowledgeFactRepository,
    KnowledgeRelationRepository,
    KnowledgeVersionRepository,
)


class InMemoryKnowledgeRepository(
    KnowledgeEntityRepository,
    KnowledgeFactRepository,
    KnowledgeRelationRepository,
    KnowledgeCollectionRepository,
    KnowledgeVersionRepository,
):
    """Unified in-memory repository implementing knowledge storage abstractions."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._entities: dict[str, KnowledgeEntity] = {}
        self._facts: dict[str, KnowledgeFact] = {}
        self._relations: dict[str, KnowledgeRelation] = {}
        self._collections: dict[str, KnowledgeCollection] = {}
        self._versions: dict[str, list[KnowledgeVersion]] = {}

    # --- Knowledge Entity Repository ---

    async def create_entity(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        async with self._lock:
            self._entities[entity.id] = entity
            return entity

    async def get_entity(self, entity_id: str) -> KnowledgeEntity | None:
        async with self._lock:
            entity = self._entities.get(entity_id)
            if not entity or entity.status == KnowledgeStatus.DELETED:
                return None
            return entity

    async def list_entities(
        self, filter_spec: KnowledgeSearchFilter
    ) -> tuple[list[KnowledgeEntity], int]:
        async with self._lock:
            return self._match_entities(filter_spec)

    async def update_entity(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        async with self._lock:
            if entity.id not in self._entities:
                raise KnowledgeEntityNotFoundError(f"Knowledge entity '{entity.id}' not found.")
            self._entities[entity.id] = entity
            return entity

    async def archive_entity(self, entity_id: str, archived_at: datetime) -> KnowledgeEntity:
        async with self._lock:
            entity = self._entities.get(entity_id)
            if not entity or entity.status == KnowledgeStatus.DELETED:
                raise KnowledgeEntityNotFoundError(f"Knowledge entity '{entity_id}' not found.")
            updated = entity.model_copy(
                update={"status": KnowledgeStatus.ARCHIVED, "archived_at": archived_at}
            )
            self._entities[entity_id] = updated
            return updated

    async def restore_entity(self, entity_id: str, updated_at: datetime) -> KnowledgeEntity:
        async with self._lock:
            entity = self._entities.get(entity_id)
            if not entity or entity.status == KnowledgeStatus.DELETED:
                raise KnowledgeEntityNotFoundError(f"Knowledge entity '{entity_id}' not found.")

            updated = entity.model_copy(
                update={
                    "status": KnowledgeStatus.ACTIVE,
                    "archived_at": None,
                    "updated_at": updated_at,
                }
            )

            self._entities[entity_id] = updated
            return updated

    async def delete_entity(
        self, entity_id: str, soft_delete: bool = True, deleted_at: datetime | None = None
    ) -> bool:
        async with self._lock:
            entity = self._entities.get(entity_id)
            if not entity:
                return False
            if soft_delete:
                d_time = deleted_at or datetime.now()
                self._entities[entity_id] = entity.model_copy(
                    update={"status": KnowledgeStatus.DELETED, "deleted_at": d_time}
                )
            else:
                del self._entities[entity_id]
            return True

    async def search_entities(
        self, filter_spec: KnowledgeSearchFilter
    ) -> tuple[list[KnowledgeEntity], int]:
        async with self._lock:
            return self._match_entities(filter_spec)

    async def count_entities(self, owner_id: str, status: KnowledgeStatus | None = None) -> int:
        async with self._lock:
            count = 0
            for e in self._entities.values():
                if e.owner_id != owner_id:
                    continue
                if status is not None and e.status != status:
                    continue
                if status is None and e.status == KnowledgeStatus.DELETED:
                    continue
                count += 1
            return count

    def _match_entities(
        self, filter_spec: KnowledgeSearchFilter
    ) -> tuple[list[KnowledgeEntity], int]:
        matched: list[KnowledgeEntity] = []
        for e in self._entities.values():
            if filter_spec.owner_id and e.owner_id != filter_spec.owner_id:
                continue
            if filter_spec.status is not None:
                if e.status != filter_spec.status:
                    continue
            else:
                if e.status == KnowledgeStatus.DELETED:
                    continue
            if filter_spec.entity_type and e.type != filter_spec.entity_type:
                continue
            if filter_spec.confidence and e.confidence != filter_spec.confidence:
                continue
            if filter_spec.collection_id and e.collection_id != filter_spec.collection_id:
                continue
            if filter_spec.query:
                q = filter_spec.query.lower()
                name_match = q in e.name.lower()
                desc_match = bool(e.description and q in e.description.lower())
                if not (name_match or desc_match):
                    continue
            if filter_spec.tags:
                entity_tags = set(e.metadata.tags)
                if not any(t in entity_tags for t in filter_spec.tags):
                    continue
            matched.append(e)

        matched.sort(key=lambda x: (x.created_at, x.id))
        total = len(matched)
        start = (filter_spec.page - 1) * filter_spec.page_size
        end = start + filter_spec.page_size
        return matched[start:end], total

    # --- Knowledge Fact Repository ---

    async def create_fact(self, fact: KnowledgeFact) -> KnowledgeFact:
        async with self._lock:
            self._facts[fact.id] = fact
            return fact

    async def get_fact(self, fact_id: str) -> KnowledgeFact | None:
        async with self._lock:
            fact = self._facts.get(fact_id)
            if not fact or fact.status == KnowledgeStatus.DELETED:
                return None
            return fact

    async def list_facts_by_entity(
        self, entity_id: str, status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE
    ) -> list[KnowledgeFact]:
        async with self._lock:
            result: list[KnowledgeFact] = []
            for f in self._facts.values():
                if f.entity_id != entity_id:
                    continue
                if status is not None and f.status != status:
                    continue
                if status is None and f.status == KnowledgeStatus.DELETED:
                    continue
                result.append(f)
            result.sort(key=lambda x: (x.created_at, x.id))
            return result

    async def list_facts(
        self,
        owner_id: str,
        predicate: str | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
        confidence: KnowledgeConfidence | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[KnowledgeFact], int]:
        async with self._lock:
            matched: list[KnowledgeFact] = []
            for f in self._facts.values():
                if f.owner_id != owner_id:
                    continue
                if status is not None and f.status != status:
                    continue
                if status is None and f.status == KnowledgeStatus.DELETED:
                    continue
                if predicate and f.predicate.lower() != predicate.lower():
                    continue
                if confidence and f.confidence != confidence:
                    continue
                matched.append(f)

            matched.sort(key=lambda x: (x.created_at, x.id))
            total = len(matched)
            start = (page - 1) * page_size
            end = start + page_size
            return matched[start:end], total

    async def update_fact(self, fact: KnowledgeFact) -> KnowledgeFact:
        async with self._lock:
            if fact.id not in self._facts:
                raise KnowledgeFactNotFoundError(f"Knowledge fact '{fact.id}' not found.")
            self._facts[fact.id] = fact
            return fact

    async def archive_fact(self, fact_id: str, archived_at: datetime) -> KnowledgeFact:
        async with self._lock:
            fact = self._facts.get(fact_id)
            if not fact or fact.status == KnowledgeStatus.DELETED:
                raise KnowledgeFactNotFoundError(f"Knowledge fact '{fact_id}' not found.")
            updated = fact.model_copy(
                update={"status": KnowledgeStatus.ARCHIVED, "archived_at": archived_at}
            )
            self._facts[fact_id] = updated
            return updated

    async def delete_fact(
        self, fact_id: str, soft_delete: bool = True, deleted_at: datetime | None = None
    ) -> bool:
        async with self._lock:
            fact = self._facts.get(fact_id)
            if not fact:
                return False
            if soft_delete:
                d_time = deleted_at or datetime.now()
                self._facts[fact_id] = fact.model_copy(
                    update={"status": KnowledgeStatus.DELETED, "deleted_at": d_time}
                )
            else:
                del self._facts[fact_id]
            return True

    # --- Knowledge Relation Repository ---

    async def create_relation(self, relation: KnowledgeRelation) -> KnowledgeRelation:
        async with self._lock:
            self._relations[relation.id] = relation
            return relation

    async def get_relation(self, relation_id: str) -> KnowledgeRelation | None:
        async with self._lock:
            rel = self._relations.get(relation_id)
            if not rel or rel.status == KnowledgeStatus.DELETED:
                return None
            return rel

    async def delete_relation(
        self, relation_id: str, soft_delete: bool = True, deleted_at: datetime | None = None
    ) -> bool:
        async with self._lock:
            rel = self._relations.get(relation_id)
            if not rel:
                return False
            if soft_delete:
                d_time = deleted_at or datetime.now()
                self._relations[relation_id] = rel.model_copy(
                    update={"status": KnowledgeStatus.DELETED, "deleted_at": d_time}
                )
            else:
                del self._relations[relation_id]
            return True

    async def list_outgoing_relations(
        self,
        entity_id: str,
        relation_type: KnowledgeRelationType | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        async with self._lock:
            res: list[KnowledgeRelation] = []
            for r in self._relations.values():
                if r.source_entity_id != entity_id:
                    continue
                if status is not None and r.status != status:
                    continue
                if status is None and r.status == KnowledgeStatus.DELETED:
                    continue
                if relation_type and r.relation_type != relation_type:
                    continue
                res.append(r)
            res.sort(key=lambda x: (x.created_at, x.id))
            return res

    async def list_incoming_relations(
        self,
        entity_id: str,
        relation_type: KnowledgeRelationType | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        async with self._lock:
            res: list[KnowledgeRelation] = []
            for r in self._relations.values():
                if r.target_entity_id != entity_id:
                    continue
                if status is not None and r.status != status:
                    continue
                if status is None and r.status == KnowledgeStatus.DELETED:
                    continue
                if relation_type and r.relation_type != relation_type:
                    continue
                res.append(r)
            res.sort(key=lambda x: (x.created_at, x.id))
            return res

    async def find_relations_between(
        self,
        source_entity_id: str,
        target_entity_id: str,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        async with self._lock:
            res: list[KnowledgeRelation] = []
            for r in self._relations.values():
                if (
                    r.source_entity_id == source_entity_id
                    and r.target_entity_id == target_entity_id
                ):
                    if status is not None and r.status != status:
                        continue
                    if status is None and r.status == KnowledgeStatus.DELETED:
                        continue
                    res.append(r)
            res.sort(key=lambda x: (x.created_at, x.id))
            return res

    # --- Knowledge Collection Repository ---

    async def create_collection(self, collection: KnowledgeCollection) -> KnowledgeCollection:
        async with self._lock:
            self._collections[collection.id] = collection
            return collection

    async def get_collection(self, collection_id: str) -> KnowledgeCollection | None:
        async with self._lock:
            col = self._collections.get(collection_id)
            if not col or col.status == KnowledgeStatus.DELETED:
                return None
            return col

    async def update_collection(self, collection: KnowledgeCollection) -> KnowledgeCollection:
        async with self._lock:
            if collection.id not in self._collections:
                raise KnowledgeCollectionNotFoundError(
                    f"Knowledge collection '{collection.id}' not found."
                )
            self._collections[collection.id] = collection
            return collection

    async def list_collections(
        self,
        owner_id: str,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[KnowledgeCollection], int]:
        async with self._lock:
            matched: list[KnowledgeCollection] = []
            for c in self._collections.values():
                if c.owner_id != owner_id:
                    continue
                if status is not None and c.status != status:
                    continue
                if status is None and c.status == KnowledgeStatus.DELETED:
                    continue
                matched.append(c)

            matched.sort(key=lambda x: (x.created_at, x.id))
            total = len(matched)
            start = (page - 1) * page_size
            end = start + page_size
            return matched[start:end], total

    async def archive_collection(
        self, collection_id: str, archived_at: datetime
    ) -> KnowledgeCollection:

        async with self._lock:
            col = self._collections.get(collection_id)
            if not col or col.status == KnowledgeStatus.DELETED:
                raise KnowledgeCollectionNotFoundError(
                    f"Knowledge collection '{collection_id}' not found."
                )
            updated = col.model_copy(
                update={"status": KnowledgeStatus.ARCHIVED, "archived_at": archived_at}
            )
            self._collections[collection_id] = updated
            return updated

    async def delete_collection(
        self, collection_id: str, soft_delete: bool = True, deleted_at: datetime | None = None
    ) -> bool:
        async with self._lock:
            col = self._collections.get(collection_id)
            if not col:
                return False
            if soft_delete:
                d_time = deleted_at or datetime.now()
                self._collections[collection_id] = col.model_copy(
                    update={"status": KnowledgeStatus.DELETED, "deleted_at": d_time}
                )
            else:
                del self._collections[collection_id]
            return True

    # --- Knowledge Version Repository ---

    async def create_version(self, version: KnowledgeVersion) -> KnowledgeVersion:
        async with self._lock:
            target_id = version.target_id
            if target_id not in self._versions:
                self._versions[target_id] = []
            self._versions[target_id].append(version)
            return version

    async def list_versions(self, target_id: str) -> list[KnowledgeVersion]:
        async with self._lock:
            versions = self._versions.get(target_id, [])
            return sorted(versions, key=lambda v: v.version_number)

    async def get_latest_version(self, target_id: str) -> KnowledgeVersion | None:
        async with self._lock:
            versions = self._versions.get(target_id, [])
            if not versions:
                return None
            return max(versions, key=lambda v: v.version_number)
