"""RAG Adapter for Module 09 Personal Knowledge integration."""

import logging

from madhav.knowledge.domain.entity import KnowledgeEntity
from madhav.knowledge.domain.fact import KnowledgeFact
from madhav.rag.domain.document import Document, DocumentSource
from madhav.rag.domain.enums import DocumentSourceType
from madhav.rag.services.indexing_service import DocumentIndexingService

logger = logging.getLogger(__name__)


class KnowledgeRAGAdapter:
    """Bridge for explicitly indexing Module 09 Personal Knowledge into Module 10 RAG Engine."""

    def __init__(self, indexing_service: DocumentIndexingService) -> None:
        self.indexing_service = indexing_service

    async def index_entity(
        self,
        entity: KnowledgeEntity,
        facts: list[KnowledgeFact] | None = None,
        metadata: dict[str, str | int | float | bool | list[str]] | None = None,
    ) -> Document:
        """Index a KnowledgeEntity and optional associated facts into RAG Engine."""
        source = DocumentSource(
            source_type=DocumentSourceType.PERSONAL_KNOWLEDGE,
            source_reference=entity.id,
        )

        content_parts = [f"Entity: {entity.name}"]
        if entity.description:
            content_parts.append(f"Description: {entity.description}")

        if facts:
            content_parts.append("Facts:")
            for f in facts:
                content_parts.append(f"- {f.predicate}: {f.value}")

        full_content = "\n".join(content_parts)

        merged_meta: dict[str, str | int | float | bool | list[str]] = {
            "entity_id": entity.id,
            "entity_type": str(entity.type),
            "name": entity.name,
        }
        if metadata:
            merged_meta.update(metadata)

        doc = await self.indexing_service.create_and_index_document(
            owner_id=entity.owner_id,
            title=f"Knowledge Entity: {entity.name}",
            content=full_content,
            source=source,
            document_type="TEXT",
            metadata=merged_meta,
        )

        logger.info("Indexed knowledge entity %s for owner %s", entity.id, entity.owner_id)
        return doc

    async def index_fact(
        self,
        fact: KnowledgeFact,
        metadata: dict[str, str | int | float | bool | list[str]] | None = None,
    ) -> Document:
        """Index a standalone KnowledgeFact into RAG Engine."""
        source = DocumentSource(
            source_type=DocumentSourceType.PERSONAL_KNOWLEDGE,
            source_reference=fact.id,
        )

        full_content = f"Fact: {fact.predicate} is {fact.value}"

        merged_meta: dict[str, str | int | float | bool | list[str]] = {
            "fact_id": fact.id,
            "entity_id": fact.entity_id,
            "predicate": fact.predicate,
        }
        if metadata:
            merged_meta.update(metadata)

        doc = await self.indexing_service.create_and_index_document(
            owner_id=fact.owner_id,
            title=f"Fact: {fact.predicate}",
            content=full_content,
            source=source,
            document_type="TEXT",
            metadata=merged_meta,
        )

        logger.info("Indexed knowledge fact %s for owner %s", fact.id, fact.owner_id)
        return doc
