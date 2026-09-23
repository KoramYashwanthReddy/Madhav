"""Module 08 — Memory Engine for MAX Personal AI platform."""

from max.memory.domain import (
    Memory,
    MemoryConfidence,
    MemoryContent,
    MemoryDuplicateResult,
    MemoryImportance,
    MemoryMetadata,
    MemoryScope,
    MemorySearchFilter,
    MemorySource,
    MemoryStatus,
    MemorySummary,
    MemoryType,
)
from max.memory.exceptions import (
    DuplicateMemoryError,
    InvalidMemoryStateTransitionError,
    MemoryDeletedError,
    MemoryEngineError,
    MemoryExpiredError,
    MemoryNotFoundError,
    MemoryOwnershipError,
    MemoryValidationError,
)
from max.memory.repositories import (
    InMemoryMemoryRepository,
    MemoryRepository,
)
from max.memory.services import (
    DeterministicDuplicateDetector,
    MemoryService,
)
from max.memory.sources import MemoryContextSource

__all__ = [
    "DeterministicDuplicateDetector",
    "DuplicateMemoryError",
    "InMemoryMemoryRepository",
    "InvalidMemoryStateTransitionError",
    "Memory",
    "MemoryConfidence",
    "MemoryContent",
    "MemoryContextSource",
    "MemoryDeletedError",
    "MemoryDuplicateResult",
    "MemoryEngineError",
    "MemoryExpiredError",
    "MemoryImportance",
    "MemoryMetadata",
    "MemoryNotFoundError",
    "MemoryOwnershipError",
    "MemoryRepository",
    "MemoryScope",
    "MemorySearchFilter",
    "MemoryService",
    "MemorySource",
    "MemoryStatus",
    "MemorySummary",
    "MemoryType",
    "MemoryValidationError",
]
