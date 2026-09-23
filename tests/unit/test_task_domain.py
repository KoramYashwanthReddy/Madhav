"""Unit tests for Module 12 Task Engine domain models and state machine."""

import pytest

from madhav.tasks.domain.enums import TaskPriority, TaskSource, TaskStatus
from madhav.tasks.domain.exceptions import InvalidTaskStateTransitionError
from madhav.tasks.domain.task import Task, TaskFailure, TaskResult
from madhav.tasks.services.state_machine import TaskStateMachine


def test_task_creation_defaults() -> None:
    """Verify task entity default field initialization."""
    task = Task(owner_id="user_123", title="Study Task")

    assert task.id.startswith("task_")
    assert task.owner_id == "user_123"
    assert task.title == "Study Task"
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.NORMAL
    assert task.progress == 0
    assert task.source == TaskSource.MANUAL
    assert task.retry_count == 0
    assert task.max_retries == 3
    assert task.retryable is True


def test_priority_ranking() -> None:
    """Verify numeric rank ordering for task priorities."""
    assert TaskPriority.LOW.rank < TaskPriority.NORMAL.rank
    assert TaskPriority.NORMAL.rank < TaskPriority.HIGH.rank
    assert TaskPriority.HIGH.rank < TaskPriority.URGENT.rank
    assert TaskPriority.URGENT.rank < TaskPriority.CRITICAL.rank


def test_valid_state_transitions() -> None:
    """Verify state machine allows valid lifecycle status transitions."""
    assert TaskStateMachine.can_transition(TaskStatus.PENDING, TaskStatus.READY)
    assert TaskStateMachine.can_transition(TaskStatus.READY, TaskStatus.IN_PROGRESS)
    assert TaskStateMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.PAUSED)
    assert TaskStateMachine.can_transition(TaskStatus.PAUSED, TaskStatus.IN_PROGRESS)
    assert TaskStateMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED)
    assert TaskStateMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.FAILED)
    assert TaskStateMachine.can_transition(TaskStatus.FAILED, TaskStatus.READY)


def test_invalid_state_transitions() -> None:
    """Verify state machine raises InvalidTaskStateTransitionError on illegal moves."""
    with pytest.raises(InvalidTaskStateTransitionError):
        TaskStateMachine.validate_transition(TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS)

    with pytest.raises(InvalidTaskStateTransitionError):
        TaskStateMachine.validate_transition(TaskStatus.CANCELLED, TaskStatus.IN_PROGRESS)

    with pytest.raises(InvalidTaskStateTransitionError):
        TaskStateMachine.validate_transition(TaskStatus.SKIPPED, TaskStatus.READY)


def test_task_result_and_failure_models() -> None:
    """Verify instantiation of TaskResult and TaskFailure models."""
    res = TaskResult(summary="Done", output_reference="art_1")
    assert res.status == TaskStatus.COMPLETED
    assert res.summary == "Done"

    fail = TaskFailure(summary="Error occurred", retryable=True)
    assert fail.error_code == "TASK_FAILED"
    assert fail.retryable is True
