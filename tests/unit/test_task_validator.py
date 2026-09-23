"""Unit tests for TaskValidator service."""

import pytest

from max.config.sections import TaskSettings
from max.tasks.domain.exceptions import (
    CircularTaskDependencyError,
    TaskHierarchyError,
    TaskValidationError,
)
from max.tasks.domain.task import Task
from max.tasks.services.validator import TaskValidator


def test_validate_task_field_limits() -> None:
    """Verify validation of title and description length boundaries."""
    settings = TaskSettings(max_title_length=10, max_description_length=20)

    # Empty title
    with pytest.raises(TaskValidationError):
        TaskValidator.validate_task(Task(owner_id="u1", title=""), settings)

    # Title too long
    with pytest.raises(TaskValidationError):
        TaskValidator.validate_task(Task(owner_id="u1", title="A" * 15), settings)

    # Description too long
    with pytest.raises(TaskValidationError):
        TaskValidator.validate_task(Task(owner_id="u1", title="Valid", description="B" * 30), settings)


def test_detect_dependency_cycle() -> None:
    """Verify DFS cycle detection for task dependencies."""
    # Graph: t1 -> t2, t2 -> t3
    graph = {
        "t1": ["t2"],
        "t2": ["t3"],
        "t3": [],
    }

    def get_outgoing(tid: str) -> list[str]:
        return graph.get(tid, [])

    # Adding t3 -> t1 should raise CircularTaskDependencyError
    with pytest.raises(CircularTaskDependencyError) as exc_info:
        TaskValidator.detect_dependency_cycle("t3", "t1", get_outgoing)

    assert "Circular task dependency" in str(exc_info.value)


def test_detect_parent_cycle() -> None:
    """Verify parent/child hierarchy loop detection."""
    tasks = {
        "parent": Task(id="parent", owner_id="u1", title="Parent"),
        "child": Task(id="child", owner_id="u1", title="Child", parent_task_id="parent"),
    }

    def get_task(tid: str) -> Task | None:
        return tasks.get(tid)

    # Setting parent's parent to child creates a cycle
    with pytest.raises(TaskHierarchyError):
        TaskValidator.detect_parent_cycle("parent", "child", get_task)


def test_check_parent_depth_limit() -> None:
    """Verify nesting depth limit check for parent tasks."""
    # Create chain of 3 levels: t1 -> t2 -> t3
    tasks = {
        "t1": Task(id="t1", owner_id="u1", title="T1"),
        "t2": Task(id="t2", owner_id="u1", title="T2", parent_task_id="t1"),
        "t3": Task(id="t3", owner_id="u1", title="T3", parent_task_id="t2"),
    }

    def get_task(tid: str) -> Task | None:
        return tasks.get(tid)

    with pytest.raises(TaskHierarchyError):
        TaskValidator.check_parent_depth("t3", get_task, max_depth=2)
