"""Unit tests for InMemoryMemoryRepository CRUD, search, and pagination."""

import pytest

from max.common.clock import DeterministicClock
from max.memory.domain.content import MemoryContent
from max.memory.domain.enums import MemoryImportance, MemoryStatus, MemoryType
from max.memory.domain.filter import MemorySearchFilter
from max.memory.domain.memory import Memory
from max.memory.repositories.memory import InMemoryMemoryRepository


@pytest.mark.asyncio
async def test_repository_crud_operations() -> None:
    """Verify repository CRUD, archive, restore, and soft delete lifecycle."""
    clock = DeterministicClock()
    repo = InMemoryMemoryRepository(clock=clock)

    mem = Memory(
        owner_id="owner_1",
        type=MemoryType.PREFERENCE,
        content=MemoryContent(text="Prefers Python over Java"),
    )
    saved = await repo.create_memory(mem)
    assert saved.memory_id == mem.memory_id

    # Retrieve
    fetched = await repo.get_memory(saved.memory_id)
    assert fetched is not None
    assert fetched.content.text == "Prefers Python over Java"

    # Update
    saved.importance = MemoryImportance.HIGH
    updated = await repo.update_memory(saved)
    assert updated.importance == MemoryImportance.HIGH

    # Archive
    archived = await repo.archive_memory(saved.memory_id)
    assert archived.status == MemoryStatus.ARCHIVED

    # Restore
    restored = await repo.restore_memory(saved.memory_id)
    assert restored.status == MemoryStatus.ACTIVE

    # Soft Delete
    deleted = await repo.delete_memory(saved.memory_id, soft_delete=True)
    assert deleted is True

    # Check existence
    assert await repo.exists(saved.memory_id) is False


@pytest.mark.asyncio
async def test_repository_search_and_pagination() -> None:
    """Verify substring text search query and pagination filtering."""
    repo = InMemoryMemoryRepository()

    m1 = Memory(owner_id="owner_1", content=MemoryContent(text="Learned Rust programming language"))
    m2 = Memory(owner_id="owner_1", content=MemoryContent(text="Building Python microservices"))
    m3 = Memory(owner_id="owner_2", content=MemoryContent(text="Different owner memory"))

    await repo.create_memory(m1)
    await repo.create_memory(m2)
    await repo.create_memory(m3)

    # Search for "python"
    results, total = await repo.search_memories(
        MemorySearchFilter(query="python", owner_id="owner_1")
    )
    assert total == 1
    assert results[0].memory_id == m2.memory_id

    # List all for owner_1
    all_results, all_total = await repo.list_memories(MemorySearchFilter(owner_id="owner_1"))
    assert all_total == 2
