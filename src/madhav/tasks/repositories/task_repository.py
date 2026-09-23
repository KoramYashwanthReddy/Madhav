"""Repository abstractions and in-memory implementation for Tasks."""

from abc import ABC, abstractmethod
from datetime import datetime

from madhav.tasks.domain.enums import TaskPriority, TaskSource, TaskStatus, TaskType
from madhav.tasks.domain.task import Task


class BaseTaskRepository(ABC):
    """Abstract repository interface for Task persistence."""

    @abstractmethod
    def save(self, task: Task) -> Task:
        """Save or update a task record."""
        ...

    @abstractmethod
    def get_by_id(self, task_id: str) -> Task | None:
        """Retrieve a task by its unique ID."""
        ...

    @abstractmethod
    def delete(self, task_id: str) -> bool:
        """Delete a task record by ID."""
        ...

    @abstractmethod
    def list_tasks(
        self,
        owner_id: str | None = None,
        group_id: str | None = None,
        plan_id: str | None = None,
        parent_task_id: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        type: TaskType | None = None,
        source: TaskSource | None = None,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        """List tasks matching filter criteria with pagination and total count."""
        ...


class MemoryTaskRepository(BaseTaskRepository):
    """In-memory thread-safe implementation of Task repository."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def save(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    def get_by_id(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def delete(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def list_tasks(
        self,
        owner_id: str | None = None,
        group_id: str | None = None,
        plan_id: str | None = None,
        parent_task_id: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        type: TaskType | None = None,
        source: TaskSource | None = None,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        filtered: list[Task] = []

        for task in self._tasks.values():
            if owner_id and task.owner_id != owner_id:
                continue
            if group_id and task.group_id != group_id:
                continue
            if plan_id and task.plan_id != plan_id:
                continue
            if parent_task_id is not None and task.parent_task_id != parent_task_id:
                continue
            if status and task.status != status:
                continue
            if priority and task.priority != priority:
                continue
            if type and task.type != type:
                continue
            if source and task.source != source:
                continue
            if due_before and (task.due_at is None or task.due_at > due_before):
                continue
            if due_after and (task.due_at is None or task.due_at < due_after):
                continue
            if search:
                query = search.lower()
                if query not in task.title.lower() and query not in task.description.lower():
                    continue

            filtered.append(task)

        # Deterministic ordering: priority DESC, due_at ASC (nulls last), created_at DESC, id ASC
        def sort_key(t: Task) -> tuple[int, float, float, str]:

            prio_rank = -t.priority.rank
            due_ts = t.due_at.timestamp() if t.due_at else float("inf")
            created_ts = -t.created_at.timestamp()
            return (prio_rank, due_ts, created_ts, t.id)

        sorted_tasks = sorted(filtered, key=sort_key)
        total_count = len(sorted_tasks)
        paginated_tasks = sorted_tasks[offset : offset + limit]

        return paginated_tasks, total_count
