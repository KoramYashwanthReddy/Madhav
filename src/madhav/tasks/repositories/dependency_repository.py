"""Repository abstractions and in-memory implementation for Task Dependencies."""

from abc import ABC, abstractmethod

from madhav.tasks.domain.dependency import TaskDependency


class BaseTaskDependencyRepository(ABC):
    """Abstract repository interface for TaskDependency persistence."""

    @abstractmethod
    def save(self, dependency: TaskDependency) -> TaskDependency:
        """Save a new task dependency relationship."""
        ...

    @abstractmethod
    def get_by_id(self, dependency_id: str) -> TaskDependency | None:
        """Retrieve a dependency by its ID."""
        ...

    @abstractmethod
    def delete(self, dependency_id: str) -> bool:
        """Delete a dependency record by ID."""
        ...

    @abstractmethod
    def get_dependencies_for_task(self, source_task_id: str) -> list[TaskDependency]:
        """Get dependencies where source_task_id depends on other tasks."""
        ...

    @abstractmethod
    def get_dependents_for_task(self, target_task_id: str) -> list[TaskDependency]:
        """Get dependencies where other tasks depend on target_task_id."""
        ...

    @abstractmethod
    def delete_by_task(self, task_id: str) -> int:
        """Delete all dependency links associated with a task ID."""
        ...


class MemoryTaskDependencyRepository(BaseTaskDependencyRepository):
    """In-memory thread-safe implementation of TaskDependency repository."""

    def __init__(self) -> None:
        self._deps: dict[str, TaskDependency] = {}

    def save(self, dependency: TaskDependency) -> TaskDependency:
        self._deps[dependency.dependency_id] = dependency
        return dependency

    def get_by_id(self, dependency_id: str) -> TaskDependency | None:
        return self._deps.get(dependency_id)

    def delete(self, dependency_id: str) -> bool:
        if dependency_id in self._deps:
            del self._deps[dependency_id]
            return True
        return False

    def get_dependencies_for_task(self, source_task_id: str) -> list[TaskDependency]:
        return [dep for dep in self._deps.values() if dep.source_task_id == source_task_id]

    def get_dependents_for_task(self, target_task_id: str) -> list[TaskDependency]:
        return [dep for dep in self._deps.values() if dep.target_task_id == target_task_id]

    def delete_by_task(self, task_id: str) -> int:
        to_delete = [
            dep_id
            for dep_id, dep in self._deps.items()
            if dep.source_task_id == task_id or dep.target_task_id == task_id
        ]
        for dep_id in to_delete:
            del self._deps[dep_id]
        return len(to_delete)
