"""Repository abstractions and memory implementations for Task Engine."""

from max.tasks.repositories.dependency_repository import (
    BaseTaskDependencyRepository,
    MemoryTaskDependencyRepository,
)
from max.tasks.repositories.group_repository import (
    BaseTaskGroupRepository,
    MemoryTaskGroupRepository,
)
from max.tasks.repositories.history_repository import (
    BaseTaskHistoryRepository,
    MemoryTaskHistoryRepository,
)
from max.tasks.repositories.task_repository import (
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
