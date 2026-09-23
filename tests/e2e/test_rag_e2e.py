"""End-to-End test for Module 10 RAG & Retrieval Engine integration."""

from datetime import UTC, datetime

import pytest

from max.ai.runtime.manager import AIRuntimeManager
from max.context.domain.item import ContextItem
from max.context.domain.policy import ContextPolicy
from max.context.domain.request import ContextRequest
from max.context.services.manager import ContextManager
from max.identity.domain.assistant import AssistantIdentity
from max.identity.domain.context import IdentityContext
from max.identity.domain.owner import OwnerIdentity
from max.identity.domain.profile import PersonalProfile
from max.knowledge.domain.entity import KnowledgeEntity
from max.knowledge.domain.enums import KnowledgeEntityType
from max.memory.domain.content import MemoryContent
from max.memory.domain.memory import Memory
from max.models.services.manager import ModelManager
from max.rag.adapters.knowledge_adapter import KnowledgeRAGAdapter
from max.rag.adapters.memory_adapter import MemoryRAGAdapter
from max.rag.domain.document import DocumentSource
from max.rag.domain.enums import DocumentSourceType
from max.rag.domain.query import RetrievalQuery
from max.rag.providers.dev_provider import DevelopmentEmbeddingProvider
from max.rag.repositories.document_repository import InMemoryDocumentRepository
from max.rag.services.context_builder import RetrievalContextBuilder
from max.rag.services.indexing_service import DocumentIndexingService
from max.rag.services.retrieval_service import RetrievalService
from max.rag.stores.memory_store import InMemoryVectorStore


@pytest.mark.asyncio
async def test_end_to_end_rag_to_context_to_ai_runtime_flow() -> None:
    """Verify complete end-to-end flow from RAG retrieval through ContextManager to AI Runtime."""
    # 1. Setup RAG Engine Subsystem
    repo = InMemoryDocumentRepository()
    vstore = InMemoryVectorStore(expected_dimensions=64)
    provider = DevelopmentEmbeddingProvider(dimensions=64)
    indexing = DocumentIndexingService(
        repository=repo, vector_store=vstore, embedding_provider=provider
    )
    retrieval = RetrievalService(vector_store=vstore, embedding_provider=provider)

    mem_adapter = MemoryRAGAdapter(indexing_service=indexing)
    k_adapter = KnowledgeRAGAdapter(indexing_service=indexing)

    # 2. Ingest a raw document
    source = DocumentSource(source_type=DocumentSourceType.TEXT, source_reference="doc-001")
    await indexing.create_and_index_document(
        owner_id="owner_1",
        title="Max Architecture Guidelines",
        content="Max follows modular clean architecture with strict subsystem boundaries.",
        source=source,
    )

    # 3. Index a memory item
    memory = Memory(
        owner_id="owner_1",
        content=MemoryContent(text="User's preferred programming language is Python 3.12."),
    )
    await mem_adapter.index_memory(memory)

    # 4. Index a knowledge entity
    now = datetime.now(UTC)
    entity = KnowledgeEntity(
        owner_id="owner_1",
        type=KnowledgeEntityType.CONCEPT,
        name="Antigravity Framework",
        description="Core agentic AI framework built by Google DeepMind.",
        created_at=now,
        updated_at=now,
    )
    await k_adapter.index_entity(entity)

    # 5. Perform retrieval search query
    query = RetrievalQuery(
        query_text="modular architecture Python programming Antigravity",
        owner_id="owner_1",
        top_k=5,
    )
    search_resp = await retrieval.retrieve(query)
    assert search_resp.total_retrieved > 0

    # 6. Transform search results into Module 06 ContextItem list via RetrievalContextBuilder
    builder = RetrievalContextBuilder()
    rag_context_items: list[ContextItem] = builder.build_context_items(search_resp.results)
    assert len(rag_context_items) > 0

    # 7. Setup ContextManager and ModelManager
    model_manager = ModelManager()
    context_manager = ContextManager(model_manager=model_manager)
    ai_runtime_manager = AIRuntimeManager()

    # Register candidate items into custom context source
    identity_ctx = IdentityContext(
        assistant=AssistantIdentity(name="Max"),
        owner=OwnerIdentity(display_name="Koram Yashwanth"),
        profile=PersonalProfile(),
    )

    ctx_request = ContextRequest(
        user_request="Summarize the system architecture for me.",
        identity_context=identity_ctx,
        model_reference="development-stub",
        policy=ContextPolicy.default(),
    )

    # Build context package
    package = await context_manager.build_context(ctx_request)
    assert package is not None

    # 8. Prepare AI request & run inference
    ai_req = await context_manager.prepare_ai_request(ctx_request)
    ai_resp = await ai_runtime_manager.generate(ai_req)

    assert ai_resp.content is not None
    assert len(ai_resp.content) > 0
