"""Repository abstractions and in-memory implementation for TaskGroups."""

from abc import ABC, abstractmethod

from max.tasks.domain.group import TaskGroup


class BaseTaskGroupRepository(ABC):
    """Abstract repository interface for TaskGroup persistence."""

    @abstractmethod
    def save(self, group: TaskGroup) -> TaskGroup:
        """Save or update a task group record."""
        ...

    @abstractmethod
    def get_by_id(self, group_id: str) -> TaskGroup | None:
        """Retrieve a task group by ID."""
        ...

    @abstractmethod
    def delete(self, group_id: str) -> bool:
        """Delete a task group record."""
        ...

    @abstractmethod
    def list_groups(
        self, owner_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> tuple[list[TaskGroup], int]:
        """List task groups matching criteria."""
        ...


class MemoryTaskGroupRepository(BaseTaskGroupRepository):
    """In-memory implementation of TaskGroup repository."""

    def __init__(self) -> None:
        self._groups: dict[str, TaskGroup] = {}

    def save(self, group: TaskGroup) -> TaskGroup:
        self._groups[group.group_id] = group
        return group

    def get_by_id(self, group_id: str) -> TaskGroup | None:
        return self._groups.get(group_id)

    def delete(self, group_id: str) -> bool:
        if group_id in self._groups:
            del self._groups[group_id]
            return True
        return False

    def list_groups(
        self, owner_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> tuple[list[TaskGroup], int]:
        filtered = [g for g in self._groups.values() if owner_id is None or g.owner_id == owner_id]
        sorted_groups = sorted(filtered, key=lambda g: g.created_at, reverse=True)
        total_count = len(sorted_groups)
        return sorted_groups[offset : offset + limit], total_count
