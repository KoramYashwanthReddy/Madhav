"""Repository abstractions and in-memory implementation for TaskHistory."""

from abc import ABC, abstractmethod

from madhav.tasks.domain.history import TaskHistoryEntry


class BaseTaskHistoryRepository(ABC):
    """Abstract repository interface for TaskHistory entry persistence."""

    @abstractmethod
    def save_entry(self, entry: TaskHistoryEntry) -> TaskHistoryEntry:
        """Record a task history event entry."""
        ...

    @abstractmethod
    def get_history_for_task(
        self, task_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[TaskHistoryEntry], int]:
        """Retrieve history entries for a task ID ordered by timestamp descending."""
        ...


class MemoryTaskHistoryRepository(BaseTaskHistoryRepository):
    """In-memory implementation of TaskHistory repository."""

    def __init__(self) -> None:
        self._history: dict[str, list[TaskHistoryEntry]] = {}

    def save_entry(self, entry: TaskHistoryEntry) -> TaskHistoryEntry:
        if entry.task_id not in self._history:
            self._history[entry.task_id] = []
        self._history[entry.task_id].append(entry)
        return entry

    def get_history_for_task(
        self, task_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[TaskHistoryEntry], int]:
        entries = self._history.get(task_id, [])
        sorted_entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)
        total_count = len(sorted_entries)
        return sorted_entries[offset : offset + limit], total_count
