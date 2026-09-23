"""Abstract base repository protocol for Memory Engine."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from madhav.memory.domain.enums import MemoryStatus
from madhav.memory.domain.filter import MemorySearchFilter
from madhav.memory.domain.memory import Memory


class MemoryRepository(Protocol):
    """Repository interface defining storage operations for memory records."""

    async def create_memory(self, memory: Memory) -> Memory:
        """Persist a new Memory aggregate."""
        ...

    async def get_memory(self, memory_id: UUID) -> Memory | None:
        """Retrieve a Memory record by ID, returning None if not found."""
        ...

    async def list_memories(self, filter_spec: MemorySearchFilter) -> tuple[list[Memory], int]:
        """Retrieve memories matching filter specification with pagination."""
        ...

    async def update_memory(self, memory: Memory) -> Memory:
        """Update properties, content, metadata, or timestamps of a memory record."""
        ...

    async def archive_memory(self, memory_id: UUID) -> Memory:
        """Transition memory record state to ARCHIVED."""
        ...

    async def restore_memory(self, memory_id: UUID) -> Memory:
        """Transition memory record state from ARCHIVED/EXPIRED back to ACTIVE."""
        ...

    async def expire_memory(self, memory_id: UUID) -> Memory:
        """Transition memory record state to EXPIRED."""
        ...

    async def delete_memory(self, memory_id: UUID, soft_delete: bool = True) -> bool:
        """Delete memory record. If soft_delete is True, mark status as DELETED."""
        ...

    async def search_memories(self, filter_spec: MemorySearchFilter) -> tuple[list[Memory], int]:
        """Execute text substring and attribute search queries across memory records."""
        ...

    async def count_memories(self, owner_id: str, status: MemoryStatus | None = None) -> int:
        """Count total matching memory records for owner."""
        ...

    async def exists(self, memory_id: UUID) -> bool:
        """Check if memory record exists."""
        ...

    async def touch_access(self, memory_id: UUID, access_time: datetime | None = None) -> None:
        """Update last_accessed_at timestamp for a memory record."""
        ...
