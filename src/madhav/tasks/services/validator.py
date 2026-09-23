"""Task validation and graph constraint checking services."""

from collections.abc import Callable

from madhav.config.sections import TaskSettings
from madhav.tasks.domain.exceptions import (
    CircularTaskDependencyError,
    InvalidTaskProgressError,
    TaskHierarchyError,
    TaskValidationError,
)
from madhav.tasks.domain.task import Task


class TaskValidator:
    """Validator for task entities, dependency graphs, and hierarchy constraints."""

    @staticmethod
    def validate_task(task: Task, settings: TaskSettings) -> None:
        """Validate task fields against configured rules and limits."""
        if not task.title or not task.title.strip():
            raise TaskValidationError("Task title cannot be empty or blank.")

        if len(task.title) > settings.max_title_length:
            raise TaskValidationError(
                f"Task title exceeds maximum allowed length of {settings.max_title_length} characters.",
                details={"title_length": len(task.title), "max_length": settings.max_title_length},
            )

        if len(task.description) > settings.max_description_length:
            raise TaskValidationError(
                f"Task description exceeds maximum allowed length of {settings.max_description_length} characters.",
                details={
                    "description_length": len(task.description),
                    "max_length": settings.max_description_length,
                },
            )

        if not (0 <= task.progress <= 100):
            raise InvalidTaskProgressError(task.progress)

    @staticmethod
    def detect_dependency_cycle(
        source_task_id: str,
        target_task_id: str,
        get_outgoing_dependencies: Callable[[str], list[str]],
    ) -> None:
        """Detect circular dependencies using DFS graph traversal.

        Checks if adding an edge (source_task_id -> target_task_id) creates a path
        from target_task_id back to source_task_id.
        """
        if source_task_id == target_task_id:
            raise CircularTaskDependencyError(cycle=[source_task_id, target_task_id])

        visited: set[str] = set()
        path: list[str] = [source_task_id, target_task_id]

        def dfs(current: str) -> bool:
            if current == source_task_id:
                return True
            if current in visited:
                return False

            visited.add(current)
            for neighbor in get_outgoing_dependencies(current):
                path.append(neighbor)
                if dfs(neighbor):
                    return True
                path.pop()

            return False

        if dfs(target_task_id):
            raise CircularTaskDependencyError(cycle=path)

    @staticmethod
    def detect_parent_cycle(
        task_id: str,
        proposed_parent_id: str,
        get_task_fn: Callable[[str], Task | None],
    ) -> None:
        """Detect parent/child hierarchy loops (e.g. A is parent of B, proposed parent of A is B)."""
        if task_id == proposed_parent_id:
            raise TaskHierarchyError(
                f"Task '{task_id}' cannot be its own parent.",
                details={"task_id": task_id, "parent_id": proposed_parent_id},
            )

        current_id: str | None = proposed_parent_id
        ancestors: list[str] = [task_id, proposed_parent_id]

        while current_id:
            parent_task = get_task_fn(current_id)
            if not parent_task:
                break
            if parent_task.parent_task_id == task_id:
                ancestors.append(task_id)
                cycle_str = " -> ".join(ancestors)
                raise TaskHierarchyError(
                    f"Circular parent-child hierarchy detected: {cycle_str}",
                    details={"cycle": ancestors},
                )
            current_id = parent_task.parent_task_id
            if current_id:
                ancestors.append(current_id)

    @staticmethod
    def check_parent_depth(
        proposed_parent_id: str,
        get_task_fn: Callable[[str], Task | None],
        max_depth: int,
    ) -> None:
        """Ensure parent hierarchy nesting depth does not exceed max_depth."""
        depth = 1
        current_id: str | None = proposed_parent_id

        while current_id:
            parent_task = get_task_fn(current_id)
            if not parent_task or not parent_task.parent_task_id:
                break
            depth += 1
            if depth >= max_depth:
                raise TaskHierarchyError(
                    f"Task parent hierarchy exceeds maximum depth limit of {max_depth}.",
                    details={"depth": depth, "max_depth": max_depth},
                )
            current_id = parent_task.parent_task_id
