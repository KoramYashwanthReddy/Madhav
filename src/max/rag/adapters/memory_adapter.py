"""RAG Adapter for Module 08 Memory Engine integration."""

import logging

from max.memory.domain.memory import Memory
from max.rag.domain.document import Document, DocumentSource
from max.rag.domain.enums import DocumentSourceType
from max.rag.services.indexing_service import DocumentIndexingService

logger = logging.getLogger(__name__)


class MemoryRAGAdapter:
    """Bridge for explicitly indexing Module 08 Memory items into Module 10 RAG Engine."""

    def __init__(self, indexing_service: DocumentIndexingService) -> None:
        self.indexing_service = indexing_service

    async def index_memory(
        self,
        memory: Memory,
        metadata: dict[str, str | int | float | bool | list[str]] | None = None,
    ) -> Document:
        """Index a single Memory instance into the RAG vector store."""
        memory_id_str = str(memory.memory_id)
        source = DocumentSource(
            source_type=DocumentSourceType.MEMORY,
            source_reference=memory_id_str,
        )

        merged_meta: dict[str, str | int | float | bool | list[str]] = {
            "memory_id": memory_id_str,
            "memory_type": str(memory.type),
            "importance": str(memory.importance),
            "confidence": str(memory.confidence),
        }
        if metadata:
            merged_meta.update(metadata)

        doc_title = f"Memory: {memory_id_str[:8]}"
        content_text = (
            memory.content.text if hasattr(memory.content, "text") else str(memory.content)
        )

        doc = await self.indexing_service.create_and_index_document(
            owner_id=memory.owner_id,
            title=doc_title,
            content=content_text,
            source=source,
            document_type="TEXT",
            metadata=merged_meta,
        )

        logger.info("Indexed memory %s for owner %s", memory_id_str, memory.owner_id)
        return doc
