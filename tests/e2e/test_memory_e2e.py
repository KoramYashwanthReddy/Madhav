"""End-to-End integration test for Module 08 Memory Engine context flow."""

import pytest

from max.context.domain.policy import ContextPolicy
from max.context.domain.request import ContextRequest
from max.context.services.manager import ContextManager
from max.memory.domain.enums import MemoryImportance, MemoryType
from max.memory.services.memory_service import MemoryService
from max.memory.sources.context import MemoryContextSource


@pytest.mark.asyncio
async def test_end_to_end_memory_to_context_flow() -> None:
    """Verify end-to-end integration where persistent memories supply context to ContextManager.

    Ensures that active memories are projected via MemoryContextSource as ContextItems
    and assembled into ContextPackage / AIRequest for Module 04 runtime generation.
    """
    memory_service = MemoryService()

    # 1. Create long-term user memories
    m1 = await memory_service.create_memory(
        owner_id="e2e_owner",
        type=MemoryType.PREFERENCE,
        text="User prefers code examples written in Python and FastAPI.",
        importance=MemoryImportance.HIGH,
    )
    m2 = await memory_service.create_memory(
        owner_id="e2e_owner",
        type=MemoryType.FACT,
        text="User is an AI infrastructure engineer based in India.",
        importance=MemoryImportance.NORMAL,
    )

    # 2. Instantiate MemoryContextSource with memories
    mem_source = MemoryContextSource(default_memories=[m1, m2])

    # 3. Instantiate ContextManager and register MemoryContextSource
    context_manager = ContextManager()
    context_manager.registry.register(mem_source)

    # 4. Construct ContextRequest
    ctx_req = ContextRequest(
        user_request="How should I design my next project architecture?",
        policy=ContextPolicy.full(),
    )

    # 5. Build ContextPackage
    package = await context_manager.build_context(ctx_req)

    # Verify memory context items are present in assembled package
    mem_items = [item for item in package.items if item.category.value == "memory"]
    assert len(mem_items) == 2
    assert any("Python and FastAPI" in item.content for item in mem_items)

    # 6. Prepare AIRequest for Module 04 Runtime
    ai_request = await context_manager.prepare_ai_request(ctx_req)
    assert len(ai_request.messages) >= 2
    # Verify contextual background message includes memory content
    bg_messages = [msg for msg in ai_request.messages if "Contextual Background:" in msg.content]
    assert len(bg_messages) == 1
    assert "Python and FastAPI" in bg_messages[0].content
