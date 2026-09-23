"""MemoryService application service facade for memory management."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from max.common.clock import Clock, SystemClock
from max.config.settings import get_settings
from max.memory.domain.content import MemoryContent
from max.memory.domain.duplicate import MemoryDuplicateResult
from max.memory.domain.enums import (
    MemoryConfidence,
    MemoryImportance,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
)
from max.memory.domain.filter import MemorySearchFilter
from max.memory.domain.memory import Memory
from max.memory.domain.metadata import MemoryMetadata
from max.memory.domain.summary import MemorySummary
from max.memory.exceptions import (
    DuplicateMemoryError,
    MemoryNotFoundError,
    MemoryOwnershipError,
    MemoryValidationError,
)
from max.memory.repositories.base import MemoryRepository
from max.memory.repositories.memory import InMemoryMemoryRepository
from max.memory.services.duplicate_detector import DeterministicDuplicateDetector

logger = logging.getLogger(__name__)


class MemoryService:
    """Service facade orchestrating memory business logic, validation, and privacy safeguards."""

    def __init__(
        self,
        repository: MemoryRepository | None = None,
        duplicate_detector: DeterministicDuplicateDetector | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._clock = clock or SystemClock()
        self._repository = repository or InMemoryMemoryRepository(clock=self._clock)
        self._duplicate_detector = duplicate_detector or DeterministicDuplicateDetector()
        self._cfg = get_settings().memory

    @property
    def repository(self) -> MemoryRepository:
        """Access underlying repository."""
        return self._repository

    async def create_memory(
        self,
        owner_id: str = "default_owner",
        type: MemoryType = MemoryType.FACT,
        text: str = "",
        structured_data: dict[str, Any] | None = None,
        importance: MemoryImportance | None = None,
        confidence: MemoryConfidence | None = None,
        source: MemorySource | None = None,
        tags: list[str] | None = None,
        metadata: MemoryMetadata | None = None,
        expires_at: datetime | None = None,
        check_duplicate: bool = True,
    ) -> Memory:
        """Create and persist a new Memory aggregate record."""

        # 1. Validation
        if not text or not text.strip():
            raise MemoryValidationError(
                "Memory text content cannot be empty or whitespace-only.",
                details={"owner_id": owner_id},
            )
        if len(text) > self._cfg.max_content_length:
            val = self._cfg.max_content_length
            raise MemoryValidationError(
                f"Memory text length ({len(text)}) exceeds maximum limit ({val}).",
                details={"max_content_length": val},
            )

        content = MemoryContent(
            text=text.strip(),
            structured_data=structured_data or {},
        )

        # 2. Duplicate Detection
        if check_duplicate and self._cfg.duplicate_detection_enabled:
            existing, _ = await self._repository.search_memories(
                MemorySearchFilter(owner_id=owner_id, limit=200)
            )
            dup_result = await self._duplicate_detector.check_duplicate(content, existing)
            if dup_result.is_duplicate:
                raise DuplicateMemoryError(
                    f"Duplicate memory detected matching memory {dup_result.existing_memory_id}.",
                    details={
                        "existing_memory_id": str(dup_result.existing_memory_id),
                        "similarity_score": dup_result.similarity_score,
                        "match_type": dup_result.match_type,
                    },
                )

        # 3. Construct Metadata
        meta = metadata or MemoryMetadata()
        if tags:
            meta.tags = list(set(meta.tags + tags))

        now = self._clock.now()

        # Resolve defaults from config if not provided
        imp = importance or MemoryImportance(self._cfg.default_importance.lower())
        conf = confidence or MemoryConfidence(self._cfg.default_confidence.lower())
        src = source or MemorySource.USER_EXPLICIT

        memory = Memory(
            owner_id=owner_id,
            type=type,
            content=content,
            status=MemoryStatus.ACTIVE,
            importance=imp,
            confidence=conf,
            source=src,
            scope=MemoryScope.USER,
            metadata=meta,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )

        saved = await self._repository.create_memory(memory)
        logger.info(
            "Created memory: memory_id=%s, type=%s, owner_id=%s",
            saved.memory_id,
            saved.type.value,
            saved.owner_id,
        )
        return saved

    async def get_memory(
        self,
        memory_id: UUID,
        owner_id: str = "default_owner",
        touch_access: bool = True,
    ) -> Memory:
        """Retrieve memory by ID with ownership verification and access tracking."""

        mem = await self._repository.get_memory(memory_id)
        if mem is None or mem.status == MemoryStatus.DELETED:
            raise MemoryNotFoundError(
                f"Memory {memory_id} not found.",
                details={"memory_id": str(memory_id)},
            )
        if mem.owner_id != owner_id:
            raise MemoryOwnershipError(
                f"Memory {memory_id} belongs to a different owner.",
                details={"memory_id": str(memory_id), "owner_id": owner_id},
            )

        # Check expiration status
        if mem.is_expired(self._clock.now()):
            if mem.status != MemoryStatus.EXPIRED:
                await self._repository.expire_memory(memory_id)
                mem.status = MemoryStatus.EXPIRED

        # Touch access timestamp
        if touch_access and self._cfg.access_tracking_enabled:
            now = self._clock.now()
            await self._repository.touch_access(memory_id, access_time=now)
            mem.last_accessed_at = now

        return mem

    async def list_memories(
        self, filter_spec: MemorySearchFilter
    ) -> tuple[list[MemorySummary], int]:
        """List memories matching search filter."""

        page_limit = min(
            filter_spec.limit if filter_spec.limit > 0 else self._cfg.default_page_size,
            self._cfg.max_page_size,
        )
        filter_spec.limit = page_limit

        memories, total = await self._repository.list_memories(filter_spec)
        summaries = [MemorySummary.from_memory(m) for m in memories]
        return summaries, total

    async def search_memories(
        self, filter_spec: MemorySearchFilter
    ) -> tuple[list[MemorySummary], int]:
        """Search memories matching filter specification."""

        page_limit = min(
            filter_spec.limit if filter_spec.limit > 0 else self._cfg.default_page_size,
            self._cfg.max_page_size,
        )
        filter_spec.limit = page_limit

        memories, total = await self._repository.search_memories(filter_spec)
        summaries = [MemorySummary.from_memory(m) for m in memories]
        return summaries, total

    async def update_memory(
        self,
        memory_id: UUID,
        owner_id: str = "default_owner",
        text: str | None = None,
        structured_data: dict[str, Any] | None = None,
        importance: MemoryImportance | None = None,
        confidence: MemoryConfidence | None = None,
        tags: list[str] | None = None,
        metadata: MemoryMetadata | None = None,
        expires_at: datetime | None = None,
    ) -> Memory:
        """Update mutable fields of a memory record."""

        mem = await self.get_memory(memory_id, owner_id=owner_id, touch_access=False)

        if text is not None:
            clean = text.strip()
            if not clean:
                raise MemoryValidationError("Updated text content cannot be empty.")
            if len(clean) > self._cfg.max_content_length:
                val = self._cfg.max_content_length
                raise MemoryValidationError(
                    f"Updated text length ({len(clean)}) exceeds maximum ({val})."
                )
            mem.content.text = clean

        if structured_data is not None:
            mem.content.structured_data = structured_data

        if importance is not None:
            mem.importance = importance

        if confidence is not None:
            mem.confidence = confidence

        if tags is not None:
            mem.metadata.tags = list(set(tags))

        if metadata is not None:
            mem.metadata = metadata

        if expires_at is not None:
            mem.expires_at = expires_at

        updated = await self._repository.update_memory(mem)
        logger.info("Updated memory: memory_id=%s, owner_id=%s", memory_id, owner_id)
        return updated

    async def archive_memory(self, memory_id: UUID, owner_id: str = "default_owner") -> Memory:
        """Archive a memory record."""
        await self.get_memory(memory_id, owner_id=owner_id, touch_access=False)
        archived = await self._repository.archive_memory(memory_id)
        logger.info("Archived memory: memory_id=%s", memory_id)
        return archived

    async def restore_memory(self, memory_id: UUID, owner_id: str = "default_owner") -> Memory:
        """Restore an archived or expired memory record back to ACTIVE."""
        raw = await self._repository.get_memory(memory_id)
        if raw is None or raw.status == MemoryStatus.DELETED:
            raise MemoryNotFoundError(f"Memory {memory_id} not found.")
        if raw.owner_id != owner_id:
            raise MemoryOwnershipError(f"Memory {memory_id} belongs to a different owner.")

        restored = await self._repository.restore_memory(memory_id)
        logger.info("Restored memory: memory_id=%s", memory_id)
        return restored

    async def expire_memory(self, memory_id: UUID, owner_id: str = "default_owner") -> Memory:
        """Explicitly transition a memory record to EXPIRED."""
        await self.get_memory(memory_id, owner_id=owner_id, touch_access=False)
        expired = await self._repository.expire_memory(memory_id)
        logger.info("Expired memory: memory_id=%s", memory_id)
        return expired

    async def delete_memory(
        self, memory_id: UUID, owner_id: str = "default_owner", soft_delete: bool = True
    ) -> bool:
        """Soft delete a memory record."""
        await self.get_memory(memory_id, owner_id=owner_id, touch_access=False)
        result = await self._repository.delete_memory(memory_id, soft_delete=soft_delete)
        logger.info("Deleted memory: memory_id=%s (soft_delete=%s)", memory_id, soft_delete)
        return result

    async def check_duplicate(
        self, content: MemoryContent, owner_id: str = "default_owner"
    ) -> MemoryDuplicateResult:
        """Check whether candidate content collides with existing memories."""
        existing, _ = await self._repository.search_memories(
            MemorySearchFilter(owner_id=owner_id, limit=200)
        )
        return await self._duplicate_detector.check_duplicate(content, existing)

    async def evaluate_expiration(self, memory_id: UUID) -> bool:
        """Evaluate and apply expiration for a memory record."""
        raw = await self._repository.get_memory(memory_id)
        if raw is None or raw.status == MemoryStatus.DELETED:
            return False
        if raw.is_expired(self._clock.now()):
            if raw.status != MemoryStatus.EXPIRED:
                await self._repository.expire_memory(memory_id)
            return True
        return False
