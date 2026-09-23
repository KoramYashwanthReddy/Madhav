"""Deterministic duplicate detection service for Personal Knowledge Engine."""

from typing import Any

from madhav.knowledge.domain.duplicate import KnowledgeDuplicateResult
from madhav.knowledge.domain.enums import KnowledgeEntityType
from madhav.knowledge.repositories.base import (
    KnowledgeEntityRepository,
    KnowledgeFactRepository,
)


class KnowledgeDuplicateDetector:
    """Deterministic duplicate entity and fact checker without LLM or vector embeddings."""

    def __init__(
        self,
        entity_repo: KnowledgeEntityRepository,
        fact_repo: KnowledgeFactRepository,
    ) -> None:
        self._entity_repo = entity_repo
        self._fact_repo = fact_repo

    async def check_duplicate_entity(
        self,
        owner_id: str,
        entity_type: KnowledgeEntityType,
        name: str,
    ) -> KnowledgeDuplicateResult:
        """Check for existing entity belonging to owner with identical type and normalized name."""
        normalized_name = name.strip().lower()
        # Retrieve all candidate active entities for owner
        from madhav.knowledge.domain.filter import KnowledgeSearchFilter

        spec = KnowledgeSearchFilter(owner_id=owner_id, page=1, page_size=200)
        entities, _ = await self._entity_repo.list_entities(spec)

        for e in entities:
            if e.type == entity_type and e.name.strip().lower() == normalized_name:
                return KnowledgeDuplicateResult(
                    is_duplicate=True,
                    matched_entity_id=e.id,
                    matched_fact_id=None,
                    similarity_score=1.0,
                    reason=(
                        f"Existing active entity '{e.name}' ({e.id}) matches "
                        "owner, type, and normalized name."
                    ),
                )

        return KnowledgeDuplicateResult(
            is_duplicate=False,
            matched_entity_id=None,
            matched_fact_id=None,
            similarity_score=0.0,
            reason=None,
        )

    async def check_duplicate_fact(
        self,
        entity_id: str,
        predicate: str,
        value: Any,
    ) -> KnowledgeDuplicateResult:
        """Check for existing fact belonging to entity with identical predicate and value."""
        norm_pred = predicate.strip().lower()
        norm_val = str(value).strip().lower()

        facts = await self._fact_repo.list_facts_by_entity(entity_id)

        for f in facts:
            if (
                f.predicate.strip().lower() == norm_pred
                and str(f.value).strip().lower() == norm_val
            ):
                return KnowledgeDuplicateResult(
                    is_duplicate=True,
                    matched_entity_id=entity_id,
                    matched_fact_id=f.id,
                    similarity_score=1.0,
                    reason=(
                        f"Existing active fact '{f.id}' matches entity_id, "
                        "predicate, and normalized value."
                    ),
                )


        return KnowledgeDuplicateResult(
            is_duplicate=False,
            matched_entity_id=None,
            matched_fact_id=None,
            similarity_score=0.0,
            reason=None,
        )
