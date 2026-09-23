"""Central business logic service for Personal Knowledge Engine."""

import logging
from datetime import datetime
from typing import Any

from madhav.common.clock import Clock, SystemClock
from madhav.knowledge.domain.collection import KnowledgeCollection
from madhav.knowledge.domain.entity import KnowledgeEntity
from madhav.knowledge.domain.enums import (
    FactValueType,
    KnowledgeConfidence,
    KnowledgeEntityType,
    KnowledgeRelationType,
    KnowledgeScope,
    KnowledgeSourceType,
    KnowledgeStatus,
)
from madhav.knowledge.domain.fact import KnowledgeFact
from madhav.knowledge.domain.filter import KnowledgeSearchFilter
from madhav.knowledge.domain.metadata import KnowledgeMetadata
from madhav.knowledge.domain.relation import KnowledgeRelation
from madhav.knowledge.domain.summary import KnowledgeSummary
from madhav.knowledge.domain.version import KnowledgeVersion
from madhav.knowledge.exceptions import (
    DuplicateKnowledgeError,
    InvalidFactValueError,
    InvalidKnowledgeRelationError,
    KnowledgeCollectionNotFoundError,
    KnowledgeEntityNotFoundError,
    KnowledgeFactNotFoundError,
    KnowledgeOwnershipError,
    KnowledgeRelationNotFoundError,
)
from madhav.knowledge.repositories.base import (
    KnowledgeCollectionRepository,
    KnowledgeEntityRepository,
    KnowledgeFactRepository,
    KnowledgeRelationRepository,
    KnowledgeVersionRepository,
)
from madhav.knowledge.services.duplicate_detector import KnowledgeDuplicateDetector

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Application facade coordinating Personal Knowledge operations and lifecycle."""

    def __init__(
        self,
        entity_repo: KnowledgeEntityRepository,
        fact_repo: KnowledgeFactRepository,
        relation_repo: KnowledgeRelationRepository,
        collection_repo: KnowledgeCollectionRepository,
        version_repo: KnowledgeVersionRepository,
        duplicate_detector: KnowledgeDuplicateDetector | None = None,
        clock: Clock | None = None,
        duplicate_detection_enabled: bool = True,
    ) -> None:
        self._entity_repo = entity_repo
        self._fact_repo = fact_repo
        self._relation_repo = relation_repo
        self._collection_repo = collection_repo
        self._version_repo = version_repo
        self._duplicate_detector = duplicate_detector or KnowledgeDuplicateDetector(
            entity_repo=entity_repo, fact_repo=fact_repo
        )
        self._clock = clock or SystemClock()
        self._duplicate_detection_enabled = duplicate_detection_enabled

    # --- Knowledge Entity Operations ---

    async def create_entity(
        self,
        owner_id: str,
        type: KnowledgeEntityType,
        name: str,
        description: str | None = None,
        confidence: KnowledgeConfidence = KnowledgeConfidence.HIGH,
        scope: KnowledgeScope = KnowledgeScope.USER,
        collection_id: str | None = None,
        metadata: KnowledgeMetadata | None = None,
        allow_duplicate: bool = False,
    ) -> KnowledgeEntity:
        """Create and persist a new Knowledge Entity with version snapshot."""

        now = self._clock.now()

        if self._duplicate_detection_enabled and not allow_duplicate:
            dup_check = await self._duplicate_detector.check_duplicate_entity(
                owner_id=owner_id, entity_type=type, name=name
            )
            if dup_check.is_duplicate:
                raise DuplicateKnowledgeError(
                    message=f"Duplicate entity candidate detected: {dup_check.reason}",
                    details={
                        "matched_entity_id": dup_check.matched_entity_id,
                        "reason": dup_check.reason,
                    },
                )

        if collection_id:
            col = await self._collection_repo.get_collection(collection_id)
            if not col or col.owner_id != owner_id or col.status == KnowledgeStatus.DELETED:
                raise KnowledgeCollectionNotFoundError(
                    f"Knowledge collection '{collection_id}' not found for owner."
                )

        entity = KnowledgeEntity(
            owner_id=owner_id,
            type=type,
            name=name,
            description=description,
            status=KnowledgeStatus.ACTIVE,
            confidence=confidence,
            scope=scope,
            collection_id=collection_id,
            metadata=metadata or KnowledgeMetadata(),
            created_at=now,
            updated_at=now,
        )

        created = await self._entity_repo.create_entity(entity)

        # Version 1 snapshot
        version = KnowledgeVersion(
            target_id=created.id,
            target_type="entity",
            version_number=1,
            snapshot=created.model_dump(mode="json"),
            changed_at=now,
            changed_by_source=KnowledgeSourceType.USER_EXPLICIT,
            change_reason="Initial entity creation",
        )
        await self._version_repo.create_version(version)

        logger.info("Knowledge entity created with ID %s for type %s", created.id, created.type)
        return created

    async def get_entity(self, entity_id: str, owner_id: str) -> KnowledgeEntity:
        """Retrieve active or archived Knowledge Entity by ID enforcing owner scoping."""
        entity = await self._entity_repo.get_entity(entity_id)
        if not entity or entity.status == KnowledgeStatus.DELETED:
            raise KnowledgeEntityNotFoundError(f"Knowledge entity '{entity_id}' not found.")
        if entity.owner_id != owner_id:
            raise KnowledgeOwnershipError(
                f"Access denied to entity '{entity_id}' due to owner mismatch."
            )
        return entity

    async def list_entities(
        self, filter_spec: KnowledgeSearchFilter
    ) -> tuple[list[KnowledgeEntity], int]:
        """List entities matching filter specifications."""
        return await self._entity_repo.list_entities(filter_spec)

    async def update_entity(
        self,
        entity_id: str,
        owner_id: str,
        name: str | None = None,
        description: str | None = None,
        confidence: KnowledgeConfidence | None = None,
        collection_id: str | None = None,
        metadata: KnowledgeMetadata | None = None,
        change_reason: str | None = None,
    ) -> KnowledgeEntity:
        """Update properties of an existing entity and append a new version snapshot."""
        existing = await self.get_entity(entity_id, owner_id)
        now = self._clock.now()

        if collection_id and collection_id != existing.collection_id:
            col = await self._collection_repo.get_collection(collection_id)
            if not col or col.owner_id != owner_id or col.status == KnowledgeStatus.DELETED:
                raise KnowledgeCollectionNotFoundError(
                    f"Knowledge collection '{collection_id}' not found for owner."
                )

        updated_fields: dict[str, Any] = {"updated_at": now}
        if name is not None:
            updated_fields["name"] = name
        if description is not None:
            updated_fields["description"] = description
        if confidence is not None:
            updated_fields["confidence"] = confidence
        if collection_id is not None:
            updated_fields["collection_id"] = collection_id
        if metadata is not None:
            updated_fields["metadata"] = metadata

        updated_entity = existing.model_copy(update=updated_fields)
        saved = await self._entity_repo.update_entity(updated_entity)

        # Version increment
        latest_ver = await self._version_repo.get_latest_version(entity_id)
        next_ver_num = (latest_ver.version_number + 1) if latest_ver else 1

        version = KnowledgeVersion(
            target_id=entity_id,
            target_type="entity",
            version_number=next_ver_num,
            snapshot=saved.model_dump(mode="json"),
            changed_at=now,
            changed_by_source=KnowledgeSourceType.USER_EXPLICIT,
            change_reason=change_reason or "Entity properties updated",
        )
        await self._version_repo.create_version(version)

        logger.info("Knowledge entity updated with ID %s", entity_id)
        return saved

    async def archive_entity(self, entity_id: str, owner_id: str) -> KnowledgeEntity:
        """Archive entity and transition status to ARCHIVED."""
        existing = await self.get_entity(entity_id, owner_id)
        if existing.status == KnowledgeStatus.ARCHIVED:
            return existing
        now = self._clock.now()
        archived = await self._entity_repo.archive_entity(entity_id, archived_at=now)
        logger.info("Knowledge entity archived with ID %s", entity_id)
        return archived

    async def restore_entity(self, entity_id: str, owner_id: str) -> KnowledgeEntity:
        """Restore an archived entity back to ACTIVE state."""
        existing = await self._entity_repo.get_entity(entity_id)
        if not existing or existing.status == KnowledgeStatus.DELETED:
            raise KnowledgeEntityNotFoundError(f"Knowledge entity '{entity_id}' not found.")
        if existing.owner_id != owner_id:
            raise KnowledgeOwnershipError(
                f"Access denied to entity '{entity_id}' due to owner mismatch."
            )
        if existing.status == KnowledgeStatus.ACTIVE:
            return existing
        now = self._clock.now()
        restored = await self._entity_repo.restore_entity(entity_id, updated_at=now)
        logger.info("Knowledge entity restored to active with ID %s", entity_id)
        return restored

    async def delete_entity(self, entity_id: str, owner_id: str, soft_delete: bool = True) -> bool:
        """Delete entity (default soft-delete) enforcing ownership."""
        await self.get_entity(entity_id, owner_id)
        now = self._clock.now()

        # Delete associated facts and relations if soft deleting
        if soft_delete:
            facts = await self._fact_repo.list_facts_by_entity(entity_id, status=None)
            for f in facts:
                await self._fact_repo.delete_fact(f.id, soft_delete=True, deleted_at=now)
            out_rels = await self._relation_repo.list_outgoing_relations(entity_id, status=None)
            for r in out_rels:
                await self._relation_repo.delete_relation(r.id, soft_delete=True, deleted_at=now)
            in_rels = await self._relation_repo.list_incoming_relations(entity_id, status=None)
            for r in in_rels:
                await self._relation_repo.delete_relation(r.id, soft_delete=True, deleted_at=now)

        result = await self._entity_repo.delete_entity(
            entity_id, soft_delete=soft_delete, deleted_at=now
        )
        logger.info("Knowledge entity deleted with ID %s (soft_delete=%s)", entity_id, soft_delete)
        return result

    async def search_entities(
        self, filter_spec: KnowledgeSearchFilter
    ) -> tuple[list[KnowledgeEntity], int]:
        """Execute deterministic search across entities."""
        return await self._entity_repo.search_entities(filter_spec)

    # --- Knowledge Fact Operations ---

    async def create_fact(
        self,
        owner_id: str,
        entity_id: str,
        subject: str,
        predicate: str,
        object: str,
        value: Any,
        value_type: FactValueType = FactValueType.TEXT,
        confidence: KnowledgeConfidence = KnowledgeConfidence.HIGH,
        source_type: KnowledgeSourceType = KnowledgeSourceType.USER_EXPLICIT,
        source_reference: dict[str, Any] | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        allow_duplicate: bool = False,
    ) -> KnowledgeFact:
        """Create and persist a new fact assertion associated with a Knowledge Entity."""
        await self.get_entity(entity_id, owner_id)
        now = self._clock.now()

        self._validate_fact_value(value, value_type)

        if self._duplicate_detection_enabled and not allow_duplicate:
            dup_check = await self._duplicate_detector.check_duplicate_fact(
                entity_id=entity_id, predicate=predicate, value=value
            )
            if dup_check.is_duplicate:
                raise DuplicateKnowledgeError(
                    message=f"Duplicate fact candidate detected: {dup_check.reason}",
                    details={
                        "matched_fact_id": dup_check.matched_fact_id,
                        "reason": dup_check.reason,
                    },
                )

        fact = KnowledgeFact(
            owner_id=owner_id,
            entity_id=entity_id,
            subject=subject,
            predicate=predicate,
            object=object,
            value=value,
            value_type=value_type,
            confidence=confidence,
            source_type=source_type,
            source_reference=source_reference,
            status=KnowledgeStatus.ACTIVE,
            valid_from=valid_from,
            valid_until=valid_until,
            created_at=now,
            updated_at=now,
        )

        created = await self._fact_repo.create_fact(fact)

        # Version 1 snapshot
        version = KnowledgeVersion(
            target_id=created.id,
            target_type="fact",
            version_number=1,
            snapshot=created.model_dump(mode="json"),
            changed_at=now,
            changed_by_source=source_type,
            change_reason="Initial fact creation",
        )
        await self._version_repo.create_version(version)

        logger.info("Knowledge fact created with ID %s for entity %s", created.id, entity_id)
        return created

    async def get_fact(self, fact_id: str, owner_id: str) -> KnowledgeFact:
        """Retrieve Knowledge Fact by ID enforcing ownership."""
        fact = await self._fact_repo.get_fact(fact_id)
        if not fact or fact.status == KnowledgeStatus.DELETED:
            raise KnowledgeFactNotFoundError(f"Knowledge fact '{fact_id}' not found.")
        if fact.owner_id != owner_id:
            raise KnowledgeOwnershipError(
                f"Access denied to fact '{fact_id}' due to owner mismatch."
            )
        return fact

    async def list_facts_by_entity(
        self,
        entity_id: str,
        owner_id: str,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeFact]:
        """List active facts for an entity after owner verification."""
        await self.get_entity(entity_id, owner_id)
        return await self._fact_repo.list_facts_by_entity(entity_id, status=status)

    async def list_facts(
        self,
        owner_id: str,
        predicate: str | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
        confidence: KnowledgeConfidence | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[KnowledgeFact], int]:
        """List facts for owner with optional predicate and confidence filters."""
        return await self._fact_repo.list_facts(
            owner_id=owner_id,
            predicate=predicate,
            status=status,
            confidence=confidence,
            page=page,
            page_size=page_size,
        )

    async def update_fact(
        self,
        fact_id: str,
        owner_id: str,
        subject: str | None = None,
        predicate: str | None = None,
        object: str | None = None,
        value: Any | None = None,
        value_type: FactValueType | None = None,
        confidence: KnowledgeConfidence | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        change_reason: str | None = None,
    ) -> KnowledgeFact:
        """Update an existing fact assertion and append a new version snapshot."""
        existing = await self.get_fact(fact_id, owner_id)
        now = self._clock.now()

        target_value_type = value_type if value_type is not None else existing.value_type
        target_value = value if value is not None else existing.value

        self._validate_fact_value(target_value, target_value_type)

        updated_fields: dict[str, Any] = {"updated_at": now}
        if subject is not None:
            updated_fields["subject"] = subject
        if predicate is not None:
            updated_fields["predicate"] = predicate
        if object is not None:
            updated_fields["object"] = object
        if value is not None:
            updated_fields["value"] = value
        if value_type is not None:
            updated_fields["value_type"] = value_type
        if confidence is not None:
            updated_fields["confidence"] = confidence
        if valid_from is not None:
            updated_fields["valid_from"] = valid_from
        if valid_until is not None:
            updated_fields["valid_until"] = valid_until

        updated_fact = existing.model_copy(update=updated_fields)
        saved = await self._fact_repo.update_fact(updated_fact)

        latest_ver = await self._version_repo.get_latest_version(fact_id)
        next_ver_num = (latest_ver.version_number + 1) if latest_ver else 1

        version = KnowledgeVersion(
            target_id=fact_id,
            target_type="fact",
            version_number=next_ver_num,
            snapshot=saved.model_dump(mode="json"),
            changed_at=now,
            changed_by_source=saved.source_type,
            change_reason=change_reason or "Fact updated",
        )
        await self._version_repo.create_version(version)

        logger.info("Knowledge fact updated with ID %s", fact_id)
        return saved

    async def archive_fact(self, fact_id: str, owner_id: str) -> KnowledgeFact:
        """Archive fact status to ARCHIVED."""
        existing = await self.get_fact(fact_id, owner_id)
        if existing.status == KnowledgeStatus.ARCHIVED:
            return existing
        now = self._clock.now()
        archived = await self._fact_repo.archive_fact(fact_id, archived_at=now)
        logger.info("Knowledge fact archived with ID %s", fact_id)
        return archived

    async def delete_fact(self, fact_id: str, owner_id: str, soft_delete: bool = True) -> bool:
        """Delete fact (default soft delete)."""
        await self.get_fact(fact_id, owner_id)
        now = self._clock.now()
        result = await self._fact_repo.delete_fact(
            fact_id, soft_delete=soft_delete, deleted_at=now
        )
        logger.info("Knowledge fact deleted with ID %s (soft_delete=%s)", fact_id, soft_delete)
        return result

    # --- Knowledge Relation Operations ---

    async def create_relation(
        self,
        owner_id: str,
        source_entity_id: str,
        relation_type: KnowledgeRelationType,
        target_entity_id: str,
        confidence: KnowledgeConfidence = KnowledgeConfidence.HIGH,
        source_type: KnowledgeSourceType = KnowledgeSourceType.USER_EXPLICIT,
        source_reference: dict[str, Any] | None = None,
        metadata: KnowledgeMetadata | None = None,
    ) -> KnowledgeRelation:
        """Create a directed relationship link between two Knowledge Entities."""
        source_ent = await self.get_entity(source_entity_id, owner_id)
        target_ent = await self.get_entity(target_entity_id, owner_id)

        if source_ent.id == target_ent.id:
            raise InvalidKnowledgeRelationError(
                "source_entity_id and target_entity_id cannot be identical."
            )

        now = self._clock.now()
        relation = KnowledgeRelation(
            owner_id=owner_id,
            source_entity_id=source_entity_id,
            relation_type=relation_type,
            target_entity_id=target_entity_id,
            confidence=confidence,
            source_type=source_type,
            source_reference=source_reference,
            metadata=metadata or KnowledgeMetadata(),
            status=KnowledgeStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        created = await self._relation_repo.create_relation(relation)
        logger.info(
            "Knowledge relation created with ID %s between %s and %s",
            created.id,
            source_entity_id,
            target_entity_id,
        )
        return created

    async def get_relation(self, relation_id: str, owner_id: str) -> KnowledgeRelation:
        """Retrieve relation by ID enforcing owner boundaries."""
        rel = await self._relation_repo.get_relation(relation_id)
        if not rel or rel.status == KnowledgeStatus.DELETED:
            raise KnowledgeRelationNotFoundError(f"Knowledge relation '{relation_id}' not found.")
        if rel.owner_id != owner_id:
            raise KnowledgeOwnershipError(
                f"Access denied to relation '{relation_id}' due to owner mismatch."
            )
        return rel

    async def delete_relation(
        self, relation_id: str, owner_id: str, soft_delete: bool = True
    ) -> bool:
        """Delete relation link."""
        await self.get_relation(relation_id, owner_id)
        now = self._clock.now()
        result = await self._relation_repo.delete_relation(
            relation_id, soft_delete=soft_delete, deleted_at=now
        )
        logger.info("Knowledge relation deleted with ID %s", relation_id)
        return result

    async def list_outgoing_relations(
        self,
        entity_id: str,
        owner_id: str,
        relation_type: KnowledgeRelationType | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        """List outgoing relations originating from an entity."""
        await self.get_entity(entity_id, owner_id)
        return await self._relation_repo.list_outgoing_relations(
            entity_id=entity_id, relation_type=relation_type, status=status
        )

    async def list_incoming_relations(
        self,
        entity_id: str,
        owner_id: str,
        relation_type: KnowledgeRelationType | None = None,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        """List incoming relations targeting an entity."""
        await self.get_entity(entity_id, owner_id)
        return await self._relation_repo.list_incoming_relations(
            entity_id=entity_id, relation_type=relation_type, status=status
        )

    async def find_relations_between(
        self,
        source_entity_id: str,
        target_entity_id: str,
        owner_id: str,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
    ) -> list[KnowledgeRelation]:
        """Find direct relations between two entities."""
        await self.get_entity(source_entity_id, owner_id)
        await self.get_entity(target_entity_id, owner_id)
        return await self._relation_repo.find_relations_between(
            source_entity_id=source_entity_id, target_entity_id=target_entity_id, status=status
        )

    # --- Knowledge Collection Operations ---

    async def create_collection(
        self,
        owner_id: str,
        name: str,
        description: str | None = None,
        metadata: KnowledgeMetadata | None = None,
    ) -> KnowledgeCollection:
        """Create and persist a new organizational collection container."""
        now = self._clock.now()
        col = KnowledgeCollection(
            owner_id=owner_id,
            name=name,
            description=description,
            metadata=metadata or KnowledgeMetadata(),
            status=KnowledgeStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        created = await self._collection_repo.create_collection(col)
        logger.info("Knowledge collection created with ID %s", created.id)
        return created

    async def get_collection(self, collection_id: str, owner_id: str) -> KnowledgeCollection:
        """Retrieve collection by ID enforcing owner scoping."""
        col = await self._collection_repo.get_collection(collection_id)
        if not col or col.status == KnowledgeStatus.DELETED:
            raise KnowledgeCollectionNotFoundError(
                f"Knowledge collection '{collection_id}' not found."
            )
        if col.owner_id != owner_id:
            raise KnowledgeOwnershipError(
                f"Access denied to collection '{collection_id}' due to owner mismatch."
            )
        return col

    async def update_collection(
        self,
        collection_id: str,
        owner_id: str,
        name: str | None = None,
        description: str | None = None,
        metadata: KnowledgeMetadata | None = None,
    ) -> KnowledgeCollection:
        """Update properties of an existing collection."""
        existing = await self.get_collection(collection_id, owner_id)
        now = self._clock.now()

        updated_fields: dict[str, Any] = {"updated_at": now}
        if name is not None:
            updated_fields["name"] = name
        if description is not None:
            updated_fields["description"] = description
        if metadata is not None:
            updated_fields["metadata"] = metadata

        updated = existing.model_copy(update=updated_fields)
        saved = await self._collection_repo.update_collection(updated)
        logger.info("Knowledge collection updated with ID %s", collection_id)
        return saved

    async def list_collections(
        self,
        owner_id: str,
        status: KnowledgeStatus | None = KnowledgeStatus.ACTIVE,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[KnowledgeCollection], int]:
        """List collections belonging to owner."""
        return await self._collection_repo.list_collections(
            owner_id=owner_id, status=status, page=page, page_size=page_size
        )

    async def archive_collection(self, collection_id: str, owner_id: str) -> KnowledgeCollection:
        """Archive collection."""
        existing = await self.get_collection(collection_id, owner_id)
        if existing.status == KnowledgeStatus.ARCHIVED:
            return existing
        now = self._clock.now()
        archived = await self._collection_repo.archive_collection(collection_id, archived_at=now)
        logger.info("Knowledge collection archived with ID %s", collection_id)
        return archived

    async def delete_collection(
        self, collection_id: str, owner_id: str, soft_delete: bool = True
    ) -> bool:
        """Delete collection."""
        await self.get_collection(collection_id, owner_id)
        now = self._clock.now()
        res = await self._collection_repo.delete_collection(
            collection_id, soft_delete=soft_delete, deleted_at=now
        )
        logger.info("Knowledge collection deleted with ID %s", collection_id)
        return res

    # --- Summary & Projection Operations ---

    async def get_knowledge_summary(self, entity_id: str, owner_id: str) -> KnowledgeSummary:
        """Construct safe aggregated summary view of an entity, active facts, and relations."""
        entity = await self.get_entity(entity_id, owner_id)
        facts = await self._fact_repo.list_facts_by_entity(
            entity_id, status=KnowledgeStatus.ACTIVE
        )
        out_rels = await self._relation_repo.list_outgoing_relations(
            entity_id, status=KnowledgeStatus.ACTIVE
        )
        in_rels = await self._relation_repo.list_incoming_relations(
            entity_id, status=KnowledgeStatus.ACTIVE
        )

        collection = None
        if entity.collection_id:
            collection = await self._collection_repo.get_collection(entity.collection_id)

        versions = await self._version_repo.list_versions(entity_id)
        version_count = len(versions) if versions else 1

        return KnowledgeSummary(
            entity=entity,
            facts=facts,
            outgoing_relations=out_rels,
            incoming_relations=in_rels,
            collection=collection,
            version_count=version_count,
        )


    # --- Fact Value Validation ---

    def _validate_fact_value(self, value: Any, value_type: FactValueType) -> None:
        """Ensure fact value matches declared value_type schema."""
        if value is None:
            raise InvalidFactValueError("Fact value cannot be None.")

        if value_type == FactValueType.TEXT:
            if not isinstance(value, str):
                raise InvalidFactValueError(
                    f"Value '{value}' must be a string for TEXT value_type."
                )

        elif value_type == FactValueType.NUMBER:
            if not isinstance(value, (int, float)):
                try:
                    float(str(value))
                except (ValueError, TypeError) as err:
                    raise InvalidFactValueError(f"Value '{value}' must be a valid number.") from err
        elif value_type == FactValueType.BOOLEAN:
            if not isinstance(value, bool):
                if str(value).lower() not in {"true", "false", "1", "0"}:
                    raise InvalidFactValueError(f"Value '{value}' must be a boolean.")
        elif value_type in (FactValueType.DATE, FactValueType.DATETIME):
            if not isinstance(value, datetime):
                if isinstance(value, str):
                    try:
                        datetime.fromisoformat(value)
                    except ValueError as err:
                        raise InvalidFactValueError(
                            f"Value '{value}' must be ISO formatted date string."
                        ) from err
                else:
                    raise InvalidFactValueError(
                        f"Value '{value}' must be a datetime or ISO string."
                    )
        elif value_type == FactValueType.REFERENCE:
            if not isinstance(value, str) or not value.strip():
                raise InvalidFactValueError(
                    "Value for REFERENCE value_type must be a non-empty string reference."
                )
        elif value_type == FactValueType.JSON:
            if not isinstance(value, (dict, list, str, int, float, bool)):
                raise InvalidFactValueError(
                    "Value for JSON value_type must be JSON-serializable object."
                )

