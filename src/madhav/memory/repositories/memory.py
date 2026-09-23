"""In-memory thread and async safe implementation of MemoryRepository."""

import asyncio
from datetime import datetime
from uuid import UUID

from madhav.common.clock import Clock, SystemClock
from madhav.memory.domain.enums import MemoryStatus
from madhav.memory.domain.filter import MemorySearchFilter
from madhav.memory.domain.memory import Memory
from madhav.memory.exceptions import (
    InvalidMemoryStateTransitionError,
    MemoryDeletedError,
    MemoryNotFoundError,
)
from madhav.memory.repositories.base import MemoryRepository


class InMemoryMemoryRepository(MemoryRepository):
    """Development in-memory repository implementing MemoryRepository.

    Thread and async safe with lock synchronization, search filtering, and lifecycle state tracking.
    """

    def __init__(self, clock: Clock | None = None) -> None:
        self._memories: dict[UUID, Memory] = {}
        self._lock = asyncio.Lock()
        self._clock: Clock = clock or SystemClock()

    async def create_memory(self, memory: Memory) -> Memory:
        async with self._lock:
            mem_copy = memory.model_copy(deep=True)
            self._memories[mem_copy.memory_id] = mem_copy
            return mem_copy.model_copy(deep=True)

    async def get_memory(self, memory_id: UUID) -> Memory | None:
        async with self._lock:
            mem = self._memories.get(memory_id)
            if mem is None:
                return None
            return mem.model_copy(deep=True)

    async def _matches_filter(self, mem: Memory, filter_spec: MemorySearchFilter) -> bool:
        # Owner check
        if mem.owner_id != filter_spec.owner_id:
            return False

        # Status check
        if filter_spec.statuses:
            if mem.status not in filter_spec.statuses:
                return False
        else:
            # Exclusions by default
            if mem.status == MemoryStatus.DELETED and not filter_spec.include_deleted:
                return False
            if mem.status == MemoryStatus.ARCHIVED and not filter_spec.include_archived:
                return False
            if mem.status == MemoryStatus.EXPIRED and not filter_spec.include_expired:
                return False

        # Type filter
        if filter_spec.types and mem.type not in filter_spec.types:
            return False

        # Importance filter
        if filter_spec.importances and mem.importance not in filter_spec.importances:
            return False

        # Source filter
        if filter_spec.sources and mem.source not in filter_spec.sources:
            return False

        # Tags filter (must match at least one tag if tags specified)
        if filter_spec.tags:
            mem_tags_set = set(mem.metadata.tags)
            if not any(tag in mem_tags_set for tag in filter_spec.tags):
                return False

        # Date range filters
        if filter_spec.created_after and mem.created_at < filter_spec.created_after:
            return False
        if filter_spec.created_before and mem.created_at > filter_spec.created_before:
            return False

        # Query substring text search
        if filter_spec.query:
            q = filter_spec.query.lower().strip()
            text_match = q in mem.content.text.lower()
            tag_match = any(q in t.lower() for t in mem.metadata.tags)
            struct_match = any(
                q in str(k).lower() or q in str(v).lower()
                for k, v in mem.content.structured_data.items()
            )
            if not (text_match or tag_match or struct_match):
                return False

        return True

    async def list_memories(self, filter_spec: MemorySearchFilter) -> tuple[list[Memory], int]:
        return await self.search_memories(filter_spec)

    async def search_memories(self, filter_spec: MemorySearchFilter) -> tuple[list[Memory], int]:
        async with self._lock:
            matching: list[Memory] = []
            for mem in self._memories.values():
                if await self._matches_filter(mem, filter_spec):
                    matching.append(mem)

            # Deterministic sorting: updated_at DESC, memory_id ASC
            matching.sort(key=lambda m: (-m.updated_at.timestamp(), str(m.memory_id)))

            total = len(matching)
            offset = max(0, filter_spec.offset)
            limit = max(1, filter_spec.limit)
            paginated = matching[offset : offset + limit]
            return [m.model_copy(deep=True) for m in paginated], total

    async def update_memory(self, memory: Memory) -> Memory:
        async with self._lock:
            existing = self._memories.get(memory.memory_id)
            if existing is None:
                raise MemoryNotFoundError(
                    f"Memory record {memory.memory_id} not found.",
                    details={"memory_id": str(memory.memory_id)},
                )
            if existing.status == MemoryStatus.DELETED:
                raise MemoryDeletedError(
                    f"Cannot update deleted memory {memory.memory_id}.",
                    details={"memory_id": str(memory.memory_id)},
                )

            updated_copy = memory.model_copy(deep=True)
            updated_copy.updated_at = self._clock.now()
            self._memories[memory.memory_id] = updated_copy
            return updated_copy.model_copy(deep=True)

    async def archive_memory(self, memory_id: UUID) -> Memory:
        async with self._lock:
            mem = self._memories.get(memory_id)
            if mem is None:
                raise MemoryNotFoundError(
                    f"Memory record {memory_id} not found.",
                    details={"memory_id": str(memory_id)},
                )
            if mem.status == MemoryStatus.DELETED:
                raise MemoryDeletedError(
                    f"Cannot archive deleted memory {memory_id}.",
                    details={"memory_id": str(memory_id)},
                )
            if mem.status == MemoryStatus.ARCHIVED:
                return mem.model_copy(deep=True)

            now = self._clock.now()
            mem.status = MemoryStatus.ARCHIVED
            mem.archived_at = now
            mem.updated_at = now
            self._memories[memory_id] = mem
            return mem.model_copy(deep=True)

    async def restore_memory(self, memory_id: UUID) -> Memory:
        async with self._lock:
            mem = self._memories.get(memory_id)
            if mem is None:
                raise MemoryNotFoundError(
                    f"Memory record {memory_id} not found.",
                    details={"memory_id": str(memory_id)},
                )
            if mem.status == MemoryStatus.DELETED:
                raise InvalidMemoryStateTransitionError(
                    f"Cannot restore deleted memory {memory_id}.",
                    details={"memory_id": str(memory_id)},
                )
            if mem.status == MemoryStatus.ACTIVE:
                return mem.model_copy(deep=True)

            now = self._clock.now()
            mem.status = MemoryStatus.ACTIVE
            mem.archived_at = None
            mem.updated_at = now
            self._memories[memory_id] = mem
            return mem.model_copy(deep=True)

    async def expire_memory(self, memory_id: UUID) -> Memory:
        async with self._lock:
            mem = self._memories.get(memory_id)
            if mem is None:
                raise MemoryNotFoundError(
                    f"Memory record {memory_id} not found.",
                    details={"memory_id": str(memory_id)},
                )
            if mem.status == MemoryStatus.DELETED:
                raise MemoryDeletedError(
                    f"Cannot expire deleted memory {memory_id}.",
                    details={"memory_id": str(memory_id)},
                )

            now = self._clock.now()
            mem.status = MemoryStatus.EXPIRED
            mem.updated_at = now
            self._memories[memory_id] = mem
            return mem.model_copy(deep=True)

    async def delete_memory(self, memory_id: UUID, soft_delete: bool = True) -> bool:
        async with self._lock:
            mem = self._memories.get(memory_id)
            if mem is None:
                raise MemoryNotFoundError(
                    f"Memory record {memory_id} not found.",
                    details={"memory_id": str(memory_id)},
                )

            if soft_delete:
                now = self._clock.now()
                mem.status = MemoryStatus.DELETED
                mem.deleted_at = now
                mem.updated_at = now
                self._memories[memory_id] = mem
            else:
                del self._memories[memory_id]
            return True

    async def count_memories(self, owner_id: str, status: MemoryStatus | None = None) -> int:
        async with self._lock:
            count = 0
            for mem in self._memories.values():
                if mem.owner_id != owner_id:
                    continue
                if status is not None:
                    if mem.status == status:
                        count += 1
                else:
                    if mem.status != MemoryStatus.DELETED:
                        count += 1
            return count

    async def exists(self, memory_id: UUID) -> bool:
        async with self._lock:
            mem = self._memories.get(memory_id)
            return mem is not None and mem.status != MemoryStatus.DELETED

    async def touch_access(self, memory_id: UUID, access_time: datetime | None = None) -> None:
        async with self._lock:
            mem = self._memories.get(memory_id)
            if mem is not None and mem.status != MemoryStatus.DELETED:
                now = access_time or self._clock.now()
                mem.last_accessed_at = now
                self._memories[memory_id] = mem
