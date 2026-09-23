"""End-to-End integration test for Module 09 Personal Knowledge Engine context projection."""

import pytest

from max.context.domain.policy import ContextPolicy
from max.context.domain.request import ContextRequest
from max.context.services.manager import ContextManager
from max.knowledge.domain.enums import (
    KnowledgeEntityType,
    KnowledgeRelationType,
    KnowledgeSourceType,
)
from max.knowledge.repositories.memory import InMemoryKnowledgeRepository
from max.knowledge.services.knowledge_service import KnowledgeService
from max.knowledge.sources.context import PersonalKnowledgeContextSource
from max.memory.domain.enums import MemoryType
from max.memory.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_end_to_end_memory_to_knowledge_to_context_flow() -> None:
    """Verify end-to-end integration:

    1. Memory Engine records raw memory
    2. Knowledge Engine creates structured entity & fact linking memory provenance
    3. Knowledge Engine connects directed relationship
    4. PersonalKnowledgeContextSource projects KnowledgeSummary to Module 06 ContextManager
    5. ContextManager builds AIRequest containing structured knowledge
    """
    memory_service = MemoryService()
    k_repo = InMemoryKnowledgeRepository()
    knowledge_service = KnowledgeService(
        entity_repo=k_repo,
        fact_repo=k_repo,
        relation_repo=k_repo,
        collection_repo=k_repo,
        version_repo=k_repo,
    )

    # 1. Create memory in Memory Engine (Module 08)
    mem = await memory_service.create_memory(
        owner_id="e2e_owner",
        type=MemoryType.FACT,
        text="The user is developing Max Personal AI runtime using Python 3.12.",
    )

    # 2. Create Knowledge Entities in Personal Knowledge Engine (Module 09)
    e_user = await knowledge_service.create_entity(
        owner_id="e2e_owner",
        type=KnowledgeEntityType.PERSON,
        name="User",
        description="System Primary Owner",
    )

    e_project = await knowledge_service.create_entity(
        owner_id="e2e_owner",
        type=KnowledgeEntityType.PROJECT,
        name="Max AI",
        description="Personal Modular AI Companion",
    )

    e_python = await knowledge_service.create_entity(
        owner_id="e2e_owner",
        type=KnowledgeEntityType.TECHNOLOGY,
        name="Python",
        description="Primary Implementation Language",
    )

    # 3. Create Fact preserving Memory Provenance
    fact = await knowledge_service.create_fact(
        owner_id="e2e_owner",
        entity_id=e_project.id,
        subject="Max AI",
        predicate="uses_language",
        object="Python",
        value="Python 3.12",
        source_type=KnowledgeSourceType.MEMORY,
        source_reference={"memory_id": str(mem.memory_id)},
    )
    assert fact.source_reference == {"memory_id": str(mem.memory_id)}

    # 4. Create Relation Link
    await knowledge_service.create_relation(
        owner_id="e2e_owner",
        source_entity_id=e_user.id,
        relation_type=KnowledgeRelationType.OWNS,
        target_entity_id=e_project.id,
    )
    await knowledge_service.create_relation(
        owner_id="e2e_owner",
        source_entity_id=e_project.id,
        relation_type=KnowledgeRelationType.USES,
        target_entity_id=e_python.id,
    )

    # 5. Retrieve Knowledge Summary projection for project entity
    summary = await knowledge_service.get_knowledge_summary(e_project.id, owner_id="e2e_owner")

    # 6. Instantiate PersonalKnowledgeContextSource
    know_source = PersonalKnowledgeContextSource(default_summaries=[summary])

    # 7. Instantiate ContextManager (Module 06) and register PersonalKnowledgeContextSource
    context_manager = ContextManager()
    context_manager.registry.register(know_source)

    # 8. Build ContextPackage
    ctx_req = ContextRequest(
        user_request="Summarize the core technologies used by Max AI.",
        policy=ContextPolicy.full(),
    )
    package = await context_manager.build_context(ctx_req)

    # Verify Knowledge ContextItem is present
    know_items = [item for item in package.items if item.category.value == "knowledge"]
    assert len(know_items) == 1
    assert "Max AI" in know_items[0].content
    assert "uses_language" in know_items[0].content

    # 9. Prepare AIRequest for Module 04 AI Runtime
    ai_request = await context_manager.prepare_ai_request(ctx_req)
    bg_messages = [msg for msg in ai_request.messages if "Contextual Background:" in msg.content]
    assert len(bg_messages) == 1
    assert "Max AI" in bg_messages[0].content
