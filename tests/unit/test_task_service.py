"""Unit tests for TaskService business logic and workflow management."""

import pytest

from madhav.reasoning.domain.enums import (
    CompletenessStatus,
    PlanStatus,
)
from madhav.reasoning.domain.plan import Plan, PlanDependency, PlanStep
from madhav.tasks.domain.enums import (
    TaskPriority,
    TaskReadinessStatus,
    TaskStatus,
    TaskType,
)
from madhav.tasks.domain.exceptions import (
    TaskRetryNotAllowedError,
)
from madhav.tasks.services.task_service import TaskService


def test_task_crud_and_lifecycle() -> None:
    """Verify task creation, retrieval, status transition, and deletion."""
    service = TaskService()

    # Create task
    task = service.create_task(
        owner_id="user_1",
        title="Deploy app",
        description="Deploy container",
        type=TaskType.MAINTENANCE,
        priority=TaskPriority.HIGH,
    )

    assert task.title == "Deploy app"
    assert task.status == TaskStatus.PENDING

    # Transition PENDING -> READY -> IN_PROGRESS -> COMPLETED
    t_ready = service.transition_task_status(task.id, TaskStatus.READY)
    assert t_ready.status == TaskStatus.READY

    t_start = service.start_task(task.id)
    assert t_start.status == TaskStatus.IN_PROGRESS
    assert t_start.started_at is not None

    t_complete = service.complete_task(task.id, result_summary="Deployed")
    assert t_complete.status == TaskStatus.COMPLETED
    assert t_complete.progress == 100
    assert t_complete.result is not None


def test_progress_update_auto_completion() -> None:
    """Verify progress updates auto-complete active tasks at 100%."""
    service = TaskService()
    task = service.create_task(owner_id="u1", title="Task 1")
    service.start_task(task.id)

    updated = service.update_progress(task.id, 100)
    assert updated.status == TaskStatus.COMPLETED
    assert updated.progress == 100


def test_pause_and_resume_task() -> None:
    """Verify pause and resume lifecycle transitions."""
    service = TaskService()
    task = service.create_task(owner_id="u1", title="Active Task")
    service.start_task(task.id)

    paused = service.pause_task(task.id)
    assert paused.status == TaskStatus.PAUSED

    resumed = service.resume_task(task.id)
    assert resumed.status == TaskStatus.IN_PROGRESS


def test_task_retry_resets_failed_task() -> None:
    """Verify retrying a FAILED task resets status to READY and increments count."""
    service = TaskService()
    task = service.create_task(owner_id="u1", title="Flaky Task", max_retries=2)
    service.start_task(task.id)
    service.transition_task_status(task.id, TaskStatus.FAILED, reason="Network timeout")

    retried = service.retry_task(task.id)
    assert retried.status == TaskStatus.READY
    assert retried.retry_count == 1

    # Retry limit enforcement
    service.start_task(task.id)
    service.transition_task_status(task.id, TaskStatus.FAILED)
    service.retry_task(task.id)  # count -> 2

    service.start_task(task.id)
    service.transition_task_status(task.id, TaskStatus.FAILED)

    with pytest.raises(TaskRetryNotAllowedError):
        service.retry_task(task.id)


def test_dependencies_and_readiness() -> None:
    """Verify task dependency linking and readiness calculation."""
    service = TaskService()
    t1 = service.create_task(owner_id="u1", title="Build")
    t2 = service.create_task(owner_id="u1", title="Deploy")

    # Link t2 DEPENDS_ON t1
    service.add_dependency(source_task_id=t2.id, target_task_id=t1.id)

    # t2 should be BLOCKED because t1 is not COMPLETED
    assert service.calculate_readiness(t2.id) == TaskReadinessStatus.BLOCKED

    # Complete t1
    service.start_task(t1.id)
    service.complete_task(t1.id)

    # t2 readiness should automatically become READY
    assert service.calculate_readiness(t2.id) == TaskReadinessStatus.READY
    assert service.get_task(t2.id).status == TaskStatus.READY


def test_task_group_summary() -> None:
    """Verify creation of task group and computation of aggregate metrics."""
    service = TaskService()
    group = service.create_task_group(owner_id="u1", name="Sprint 1")

    t1 = service.create_task(owner_id="u1", title="T1", group_id=group.group_id)
    service.create_task(owner_id="u1", title="T2", group_id=group.group_id)

    service.start_task(t1.id)
    service.complete_task(t1.id)  # progress=100

    summary = service.get_task_group_summary(group.group_id)
    assert summary.total_tasks == 2
    assert summary.completed_tasks == 1
    assert summary.pending_tasks == 1
    assert summary.overall_progress == 50.0


def test_generate_tasks_from_plan_idempotency() -> None:
    """Verify idempotent task generation from Module 11 Reasoning Plan."""
    service = TaskService()

    plan = Plan(
        plan_id="plan_123",
        title="Test Plan",
        description="Plan Description",
        reasoning_id="reas_1",
        owner_id="u1",
        version=1,
        steps=[
            PlanStep(sequence=1, step_id="s1", title="Step 1", description="Desc 1"),
            PlanStep(
                sequence=2,
                step_id="s2",
                title="Step 2",
                description="Desc 2",
                dependencies=["s1"],
            ),
        ],
        dependencies=[PlanDependency(source_step_id="s1", target_step_id="s2")],
        status=PlanStatus.ACTIVE,
        completeness=CompletenessStatus.COMPLETE,
    )



    tasks1, deps1 = service.generate_tasks_from_plan(plan)
    assert len(tasks1) == 2
    assert len(deps1) == 1

    # Re-run plan conversion for same plan & version
    tasks2, deps2 = service.generate_tasks_from_plan(plan)
    assert len(tasks2) == 2
    assert tasks1[0].id == tasks2[0].id  # Preserves existing task IDs!
