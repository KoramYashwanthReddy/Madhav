"""Unit tests for RAG IndexingService, RetrievalService, ContextBuilder, and Adapters."""

from datetime import UTC, datetime

import pytest

from max.knowledge.domain.entity import KnowledgeEntity
from max.knowledge.domain.enums import KnowledgeEntityType
from max.knowledge.domain.fact import KnowledgeFact
from max.memory.domain.content import MemoryContent
from max.memory.domain.memory import Memory
from max.rag.adapters.knowledge_adapter import KnowledgeRAGAdapter
from max.rag.adapters.memory_adapter import MemoryRAGAdapter
from max.rag.domain.document import DocumentSource
from max.rag.domain.enums import DocumentSourceType, DocumentStatus
from max.rag.domain.query import RetrievalQuery
from max.rag.providers.dev_provider import DevelopmentEmbeddingProvider
from max.rag.repositories.document_repository import InMemoryDocumentRepository
from max.rag.services.context_builder import RetrievalContextBuilder
from max.rag.services.indexing_service import DocumentIndexingService
from max.rag.services.retrieval_service import RetrievalService
from max.rag.stores.memory_store import InMemoryVectorStore


@pytest.fixture
def rag_components():
    """Fixture providing initialized repository, vector store, embedding provider, and services."""
    repo = InMemoryDocumentRepository()
    vstore = InMemoryVectorStore(expected_dimensions=64)
    provider = DevelopmentEmbeddingProvider(dimensions=64)
    indexing = DocumentIndexingService(
        repository=repo, vector_store=vstore, embedding_provider=provider
    )
    retrieval = RetrievalService(vector_store=vstore, embedding_provider=provider)
    return repo, vstore, provider, indexing, retrieval


@pytest.mark.asyncio
async def test_indexing_pipeline_and_idempotency(rag_components) -> None:
    """Test full document indexing pipeline, content hashing, and idempotency."""
    _, _, _, indexing, _ = rag_components

    source = DocumentSource(source_type=DocumentSourceType.TEXT, source_reference="ref-1")
    content = "This is a test document content for indexing."

    # First indexing call
    doc1 = await indexing.create_and_index_document(
        owner_id="u1",
        title="Doc 1",
        content=content,
        source=source,
    )
    assert doc1.status == DocumentStatus.INDEXED
    assert doc1.content_hash is not None

    # Duplicate creation with identical content hash -> idempotency
    doc2 = await indexing.create_and_index_document(
        owner_id="u1",
        title="Doc 1 Duplicate",
        content=content,
        source=source,
    )
    assert doc2.id == doc1.id


@pytest.mark.asyncio
async def test_reindexing_and_deletion(rag_components) -> None:
    """Test updating content, reindexing, and document soft-deletion."""
    repo, vstore, _, indexing, retrieval = rag_components

    source = DocumentSource(source_type=DocumentSourceType.TEXT, source_reference="ref-2")
    doc = await indexing.create_and_index_document(
        owner_id="u1",
        title="Original Title",
        content="Original content string.",
        source=source,
    )

    # Search finds original content
    q1 = RetrievalQuery(query_text="Original content", owner_id="u1")
    res1 = await retrieval.retrieve(q1)
    assert len(res1.results) > 0

    # Reindex with updated content
    await indexing.reindex_document(doc.id, new_content="Updated content string.")
    updated_doc = await repo.get_by_id(doc.id)
    assert updated_doc is not None
    assert updated_doc.content == "Updated content string."

    # Soft delete document
    await indexing.delete_document(doc.id)
    deleted_doc = await repo.get_by_id(doc.id)
    assert deleted_doc is not None
    assert deleted_doc.status == DocumentStatus.DELETED

    # Search should no longer return deleted document
    q2 = RetrievalQuery(query_text="Updated content", owner_id="u1")
    res2 = await retrieval.retrieve(q2)
    assert len(res2.results) == 0


@pytest.mark.asyncio
async def test_retrieval_context_builder(rag_components) -> None:
    """Test converting retrieval results into Module 06 ContextItems."""
    _, _, _, indexing, retrieval = rag_components

    source = DocumentSource(source_type=DocumentSourceType.TEXT, source_reference="ref-3")
    await indexing.create_and_index_document(
        owner_id="u1",
        title="Architecture Doc",
        content="Max system uses modular architecture.",
        source=source,
    )

    q = RetrievalQuery(query_text="modular architecture", owner_id="u1")
    resp = await retrieval.retrieve(q)

    builder = RetrievalContextBuilder(max_characters=1000)
    items = builder.build_context_items(resp.results)

    assert len(items) > 0
    assert items[0].source.startswith("rag_retrieval:")
    assert "Architecture Doc" in items[0].content
    assert items[0].metadata["document_id"] is not None


@pytest.mark.asyncio
async def test_memory_and_knowledge_adapters(rag_components) -> None:
    """Test MemoryRAGAdapter and KnowledgeRAGAdapter integration."""
    _, _, _, indexing, retrieval = rag_components

    mem_adapter = MemoryRAGAdapter(indexing_service=indexing)
    k_adapter = KnowledgeRAGAdapter(indexing_service=indexing)

    # 1. Memory item indexing
    memory = Memory(
        owner_id="u1",
        content=MemoryContent(text="User prefers dark theme for IDE."),
    )
    mem_doc = await mem_adapter.index_memory(memory)
    assert mem_doc.source.source_type == DocumentSourceType.MEMORY
    assert mem_doc.source.source_reference == str(memory.memory_id)

    # 2. Knowledge entity indexing
    now = datetime.now(UTC)
    entity = KnowledgeEntity(
        owner_id="u1",
        type=KnowledgeEntityType.CONCEPT,
        name="Python Programming",
        description="Core language for AI development.",
        created_at=now,
        updated_at=now,
    )
    fact = KnowledgeFact(
        owner_id="u1",
        entity_id=entity.id,
        subject="Python",
        predicate="is_version",
        object="3.12",
        value="3.12",
        created_at=now,
        updated_at=now,
    )
    k_doc = await k_adapter.index_entity(entity, facts=[fact])
    assert k_doc.source.source_type == DocumentSourceType.PERSONAL_KNOWLEDGE
    assert k_doc.source.source_reference == entity.id

    # Search retrieves indexed memory and knowledge
    res_mem = await retrieval.retrieve(RetrievalQuery(query_text="dark theme", owner_id="u1"))
    assert len(res_mem.results) > 0
    assert res_mem.results[0].source.source_type == DocumentSourceType.MEMORY

    res_k = await retrieval.retrieve(RetrievalQuery(query_text="Python Programming", owner_id="u1"))
    assert len(res_k.results) > 0
    assert res_k.results[0].source.source_type == DocumentSourceType.PERSONAL_KNOWLEDGE
