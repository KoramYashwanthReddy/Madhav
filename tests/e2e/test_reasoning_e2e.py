"""End-to-End tests for Module 11 Reasoning & Planning engine."""

import pytest

from madhav.context.services.manager import ContextManager
from madhav.conversation.repositories.memory import InMemoryConversationRepository
from madhav.conversation.services.conversation_service import ConversationService
from madhav.knowledge.repositories.memory import InMemoryKnowledgeRepository
from madhav.knowledge.services.knowledge_service import KnowledgeService
from madhav.memory.repositories import InMemoryMemoryRepository
from madhav.memory.services import MemoryService
from madhav.rag.repositories.document_repository import InMemoryDocumentRepository
from madhav.reasoning.domain import (
    ReasoningMode,
    ReasoningObjective,
    ReasoningRequest,
    ReasoningStatus,
)
from madhav.reasoning.providers import DevelopmentReasoningProvider
from madhav.reasoning.repositories import InMemoryReasoningRepository
from madhav.reasoning.services import ReasoningService


@pytest.mark.asyncio
async def test_e2e_reasoning_pipeline_with_upstream_modules() -> None:
    """End-to-end test validating Module 11 reasoning pipeline."""
    owner_id = "user_e2e_1"

    # Setup upstream modules
    mem_repo = InMemoryMemoryRepository()
    mem_service = MemoryService(repository=mem_repo)
    await mem_service.create_memory(
        owner_id=owner_id,
        text="User works 40 hours a week on Python backend project HirrApp",
    )

    know_repo = InMemoryKnowledgeRepository()
    _ = KnowledgeService(
        entity_repo=know_repo,
        fact_repo=know_repo,
        relation_repo=know_repo,
        collection_repo=know_repo,
        version_repo=know_repo,
    )

    conv_repo = InMemoryConversationRepository()
    conv_service = ConversationService(repository=conv_repo)
    _ = await conv_service.create_conversation(
        owner_id=owner_id, title="Architecture Discussion"
    )

    _ = InMemoryDocumentRepository()

    ctx_manager = ContextManager()

    # Setup Module 11 Reasoning Engine
    reasoning_repo = InMemoryReasoningRepository()
    reasoning_provider = DevelopmentReasoningProvider()
    reasoning_service = ReasoningService(
        reasoning_repository=reasoning_repo,
        reasoning_provider=reasoning_provider,
        context_manager=ctx_manager,
    )

    # Execute Reasoning Request
    obj = ReasoningObjective(
        title="Deploy HirrApp Service",
        description="Create step-by-step architectural deployment plan for HirrApp",
        desired_outcome="Production deployment ready plan",
    )
    req = ReasoningRequest(
        owner_id=owner_id,
        objective=obj,
        mode=ReasoningMode.PLANNING,
    )

    result = await reasoning_service.execute_reasoning(req)

    # Verifications
    assert result.status == ReasoningStatus.COMPLETED
    assert result.request_id == req.id
    assert result.plan is not None
    assert len(result.plan["steps"]) >= 3
    assert result.confidence.value in ["LOW", "MEDIUM", "HIGH"]

    # Verify structured observations preserved evidence
    assert len(result.observations) > 0

    # Verify zero execution occurred (all steps remain PENDING or READY)
    for step in result.plan["steps"]:
        st = str(step["status"].value if hasattr(step["status"], "value") else step["status"])
        assert st in ("PENDING", "READY")
