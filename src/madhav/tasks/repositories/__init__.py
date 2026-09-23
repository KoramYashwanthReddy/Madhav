"""Repository abstractions and memory implementations for Task Engine."""

from madhav.tasks.repositories.dependency_repository import (
    BaseTaskDependencyRepository,
    MemoryTaskDependencyRepository,
)
from madhav.tasks.repositories.group_repository import (
    BaseTaskGroupRepository,
    MemoryTaskGroupRepository,
)
from madhav.tasks.repositories.history_repository import (
    BaseTaskHistoryRepository,
    MemoryTaskHistoryRepository,
)
from madhav.tasks.repositories.task_repository import (
    BaseTaskRepository,
    MemoryTaskRepository,
)

__all__ = [
    "BaseTaskRepository",
    "MemoryTaskRepository",
    "BaseTaskDependencyRepository",
    "MemoryTaskDependencyRepository",
    "BaseTaskGroupRepository",
    "MemoryTaskGroupRepository",
    "BaseTaskHistoryRepository",
    "MemoryTaskHistoryRepository",
]
