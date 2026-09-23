"""Task Engine service providing business logic for task lifecycle management."""

import logging
from datetime import datetime
from typing import Any

from max.config.sections import TaskSettings
from max.reasoning.domain.plan import Plan
from max.tasks.domain.dependency import TaskDependency
from max.tasks.domain.enums import (
    DependencyType,
    TaskGroupStatus,
    TaskPriority,
    TaskReadinessStatus,
    TaskSource,
    TaskStatus,
    TaskType,
)
from max.tasks.domain.exceptions import (
    InvalidTaskProgressError,
    TaskCancelledError,
    TaskGroupNotFoundError,
    TaskGroupOwnershipError,
    TaskNotFoundError,
    TaskOwnershipError,
    TaskRetryNotAllowedError,
)
from max.tasks.domain.group import TaskGroup, TaskGroupSummary
from max.tasks.domain.history import TaskHistoryEntry
from max.tasks.domain.references import TaskReference
from max.tasks.domain.schedule import TaskSchedule
from max.tasks.domain.task import Task, TaskResult
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
from max.tasks.services.plan_mapper import PlanTaskMapper
from max.tasks.services.state_machine import TaskStateMachine
from max.tasks.services.validator import TaskValidator

logger = logging.getLogger(__name__)


class TaskService:
    """Core domain service for Managing Tasks, Groups, Dependencies, and Plan Conversion."""

    def __init__(
        self,
        task_repository: BaseTaskRepository | None = None,
        dependency_repository: BaseTaskDependencyRepository | None = None,
        group_repository: BaseTaskGroupRepository | None = None,
        history_repository: BaseTaskHistoryRepository | None = None,
        settings: TaskSettings | None = None,
    ) -> None:
        self.task_repo = task_repository or MemoryTaskRepository()
        self.dep_repo = dependency_repository or MemoryTaskDependencyRepository()
        self.group_repo = group_repository or MemoryTaskGroupRepository()
        self.history_repo = history_repository or MemoryTaskHistoryRepository()
        self.settings = settings or TaskSettings()

    def create_task(
        self,
        owner_id: str,
        title: str,
        description: str = "",
        type: TaskType = TaskType.GENERAL,
        priority: TaskPriority = TaskPriority.NORMAL,
        source: TaskSource = TaskSource.MANUAL,
        plan_id: str | None = None,
        plan_version: int | None = None,
        plan_step_id: str | None = None,
        reasoning_id: str | None = None,
        conversation_id: str | None = None,
        parent_task_id: str | None = None,
        group_id: str | None = None,
        schedule: TaskSchedule | None = None,
        due_at: datetime | None = None,
        references: list[TaskReference] | None = None,
        metadata: dict[str, Any] | None = None,
        max_retries: int | None = None,
    ) -> Task:
        """Create a new Task record."""
        if parent_task_id:
            TaskValidator.check_parent_depth(
                proposed_parent_id=parent_task_id,
                get_task_fn=self.task_repo.get_by_id,
                max_depth=self.settings.max_parent_depth,
            )

        if group_id:
            group = self.group_repo.get_by_id(group_id)
            if not group:
                raise TaskGroupNotFoundError(group_id)
            if group.owner_id != owner_id:
                raise TaskGroupOwnershipError(group_id, group.owner_id, owner_id)

        task = Task(
            owner_id=owner_id,
            title=title,
            description=description,
            type=type,
            status=TaskStatus.PENDING,
            priority=priority,
            progress=0,
            source=source,
            plan_id=plan_id,
            plan_version=plan_version,
            plan_step_id=plan_step_id,
            reasoning_id=reasoning_id,
            conversation_id=conversation_id,
            parent_task_id=parent_task_id,
            group_id=group_id,
            schedule=schedule,
            due_at=due_at,
            max_retries=max_retries if max_retries is not None else self.settings.max_retries,
            references=references or [],
            metadata=metadata or {},
        )

        TaskValidator.validate_task(task, self.settings)
        saved_task = self.task_repo.save(task)

        # Record history
        self._record_history(
            task_id=saved_task.id,
            previous_status=None,
            new_status=saved_task.status,
            reason="Task created",
            actor=owner_id,
        )

        logger.info("Task created", extra={"task_id": saved_task.id, "status": saved_task.status.value, "owner_id": owner_id})
        return saved_task

    def get_task(self, task_id: str, requesting_owner_id: str | None = None) -> Task:
        """Retrieve task by ID with optional owner verification."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        if requesting_owner_id and task.owner_id != requesting_owner_id:
            raise TaskOwnershipError(task_id, task.owner_id, requesting_owner_id)
        return task

    def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: TaskPriority | None = None,
        type: TaskType | None = None,
        due_at: datetime | None = None,
        group_id: str | None = None,
        parent_task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        requesting_owner_id: str | None = None,
    ) -> Task:
        """Update task properties."""
        task = self.get_task(task_id, requesting_owner_id)

        if parent_task_id is not None and parent_task_id != task.parent_task_id:
            if parent_task_id:
                TaskValidator.detect_parent_cycle(task_id, parent_task_id, self.task_repo.get_by_id)
                TaskValidator.check_parent_depth(parent_task_id, self.task_repo.get_by_id, self.settings.max_parent_depth)

        if group_id is not None and group_id != task.group_id:
            if group_id:
                group = self.group_repo.get_by_id(group_id)
                if not group:
                    raise TaskGroupNotFoundError(group_id)
                if group.owner_id != task.owner_id:
                    raise TaskGroupOwnershipError(group_id, group.owner_id, task.owner_id)

        updated_dict = task.model_dump()
        if title is not None:
            updated_dict["title"] = title
        if description is not None:
            updated_dict["description"] = description
        if priority is not None:
            updated_dict["priority"] = priority
        if type is not None:
            updated_dict["type"] = type
        if due_at is not None:
            updated_dict["due_at"] = due_at
        if group_id is not None:
            updated_dict["group_id"] = group_id
        if parent_task_id is not None:
            updated_dict["parent_task_id"] = parent_task_id
        if metadata is not None:
            merged_meta = dict(task.metadata)
            merged_meta.update(metadata)
            updated_dict["metadata"] = merged_meta

        updated_dict["updated_at"] = datetime.utcnow()
        updated_task = Task(**updated_dict)

        TaskValidator.validate_task(updated_task, self.settings)
        saved = self.task_repo.save(updated_task)

        self._record_history(
            task_id=saved.id,
            previous_status=saved.status,
            new_status=saved.status,
            reason="Task updated",
            actor=requesting_owner_id or saved.owner_id,
        )

        return saved

    def delete_task(self, task_id: str, requesting_owner_id: str | None = None) -> bool:
        """Delete a task and its associated dependencies."""
        task = self.get_task(task_id, requesting_owner_id)
        self.dep_repo.delete_by_task(task_id)
        deleted = self.task_repo.delete(task_id)
        if deleted:
            logger.info("Task deleted", extra={"task_id": task_id, "owner_id": task.owner_id})
        return deleted

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
        """List tasks matching query parameters."""
        effective_limit = min(limit, self.settings.max_page_size)
        return self.task_repo.list_tasks(
            owner_id=owner_id,
            group_id=group_id,
            plan_id=plan_id,
            parent_task_id=parent_task_id,
            status=status,
            priority=priority,
            type=type,
            source=source,
            due_before=due_before,
            due_after=due_after,
            search=search,
            limit=effective_limit,
            offset=offset,
        )

    def transition_task_status(
        self,
        task_id: str,
        target_status: TaskStatus,
        reason: str = "Status transition",
        actor: str = "system",
        requesting_owner_id: str | None = None,
    ) -> Task:
        """Transition task to a new status using TaskStateMachine."""
        task = self.get_task(task_id, requesting_owner_id)
        TaskStateMachine.validate_transition(task.status, target_status, reason=reason)

        now = datetime.utcnow()
        updated_dict = task.model_dump()
        updated_dict["status"] = target_status
        updated_dict["updated_at"] = now

        if target_status == TaskStatus.IN_PROGRESS and task.started_at is None:
            updated_dict["started_at"] = now

        if target_status == TaskStatus.COMPLETED:
            updated_dict["completed_at"] = now
            updated_dict["progress"] = 100
            if task.result is None:
                updated_dict["result"] = TaskResult(
                    status=TaskStatus.COMPLETED,
                    summary="Task completed successfully",
                    completed_at=now,
                )

        if target_status == TaskStatus.CANCELLED:
            updated_dict["cancelled_at"] = now

        new_task = Task(**updated_dict)
        saved_task = self.task_repo.save(new_task)

        self._record_history(
            task_id=saved_task.id,
            previous_status=task.status,
            new_status=target_status,
            reason=reason,
            actor=actor,
        )

        # Deterministically cancel child tasks if parent cancelled
        if target_status == TaskStatus.CANCELLED:
            self._cancel_child_tasks(task_id, actor=actor)

        # Notify dependents / re-evaluate readiness
        self._evaluate_dependents_readiness(task_id)

        logger.info(
            "Task status updated",
            extra={
                "task_id": saved_task.id,
                "previous_status": task.status.value,
                "new_status": target_status.value,
                "progress": saved_task.progress,
            },
        )
        return saved_task

    def update_progress(
        self,
        task_id: str,
        progress: int,
        reason: str = "Progress updated",
        requesting_owner_id: str | None = None,
    ) -> Task:
        """Update task progress percentage (0 to 100)."""
        if not (0 <= progress <= 100):
            raise InvalidTaskProgressError(progress)

        task = self.get_task(task_id, requesting_owner_id)

        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.SKIPPED):
            if task.status == TaskStatus.COMPLETED and progress < 100:
                raise InvalidTaskProgressError(progress, "Completed task progress cannot be decreased.")
            if task.status == TaskStatus.CANCELLED:
                raise TaskCancelledError(task_id)

        updated_dict = task.model_dump()
        updated_dict["progress"] = progress
        updated_dict["updated_at"] = datetime.utcnow()

        if progress == 100 and task.status == TaskStatus.IN_PROGRESS:
            return self.complete_task(
                task_id=task_id,
                result_summary="Task completed at 100% progress",
                requesting_owner_id=requesting_owner_id,
            )

        new_task = Task(**updated_dict)
        saved = self.task_repo.save(new_task)

        self._record_history(
            task_id=saved.id,
            previous_status=saved.status,
            new_status=saved.status,
            reason=f"Progress updated to {progress}%",
            details={"progress": progress, "reason": reason},
        )
        return saved

    # Lifecycle Action Helpers (No Action Execution!)
    def start_task(self, task_id: str, requesting_owner_id: str | None = None) -> Task:
        """Lifecycle action: Move task to IN_PROGRESS. DOES NOT EXECUTE ACTIVE ACTIONS."""
        return self.transition_task_status(
            task_id=task_id,
            target_status=TaskStatus.IN_PROGRESS,
            reason="Task started",
            actor=requesting_owner_id or "user",
            requesting_owner_id=requesting_owner_id,
        )

    def pause_task(self, task_id: str, requesting_owner_id: str | None = None) -> Task:
        """Lifecycle action: Move active task to PAUSED."""
        return self.transition_task_status(
            task_id=task_id,
            target_status=TaskStatus.PAUSED,
            reason="Task paused",
            actor=requesting_owner_id or "user",
            requesting_owner_id=requesting_owner_id,
        )

    def resume_task(self, task_id: str, requesting_owner_id: str | None = None) -> Task:
        """Lifecycle action: Move paused task back to IN_PROGRESS."""
        return self.transition_task_status(
            task_id=task_id,
            target_status=TaskStatus.IN_PROGRESS,
            reason="Task resumed",
            actor=requesting_owner_id or "user",
            requesting_owner_id=requesting_owner_id,
        )

    def complete_task(
        self,
        task_id: str,
        result_summary: str = "Task completed",
        output_reference: str | None = None,
        metadata: dict[str, Any] | None = None,
        requesting_owner_id: str | None = None,
    ) -> Task:
        """Lifecycle action: Mark task as COMPLETED."""
        task = self.get_task(task_id, requesting_owner_id)
        if task.status == TaskStatus.COMPLETED:
            return task

        now = datetime.utcnow()
        result = TaskResult(
            status=TaskStatus.COMPLETED,
            summary=result_summary,
            output_reference=output_reference,
            completed_at=now,
            metadata=metadata or {},
        )

        updated_dict = task.model_dump()
        updated_dict["result"] = result
        new_task = Task(**updated_dict)
        self.task_repo.save(new_task)

        return self.transition_task_status(
            task_id=task_id,
            target_status=TaskStatus.COMPLETED,
            reason="Task completed",
            actor=requesting_owner_id or "user",
            requesting_owner_id=requesting_owner_id,
        )

    def cancel_task(self, task_id: str, reason: str = "Task cancelled", requesting_owner_id: str | None = None) -> Task:
        """Lifecycle action: Cancel task and child subtasks."""
        return self.transition_task_status(
            task_id=task_id,
            target_status=TaskStatus.CANCELLED,
            reason=reason,
            actor=requesting_owner_id or "user",
            requesting_owner_id=requesting_owner_id,
        )

    def retry_task(
        self,
        task_id: str,
        reason: str = "Retry reset requested",
        requesting_owner_id: str | None = None,
    ) -> Task:
        """Retry reset: Transition FAILED task back to READY if retryable."""
        task = self.get_task(task_id, requesting_owner_id)

        if task.status != TaskStatus.FAILED:
            raise TaskRetryNotAllowedError(task_id, f"Task status is '{task.status.value}', not FAILED.")

        if not task.retryable:
            raise TaskRetryNotAllowedError(task_id, "Task is marked non-retryable.")

        if task.retry_count >= task.max_retries:
            raise TaskRetryNotAllowedError(
                task_id, f"Retry count limit reached ({task.retry_count}/{task.max_retries})."
            )

        now = datetime.utcnow()
        updated_dict = task.model_dump()
        updated_dict["status"] = TaskStatus.READY
        updated_dict["retry_count"] = task.retry_count + 1
        updated_dict["last_retry_at"] = now
        updated_dict["updated_at"] = now
        updated_dict["failure"] = None  # Reset failure status on retry

        reset_task = Task(**updated_dict)
        saved = self.task_repo.save(reset_task)

        self._record_history(
            task_id=saved.id,
            previous_status=TaskStatus.FAILED,
            new_status=TaskStatus.READY,
            reason=f"Task retried ({saved.retry_count}/{saved.max_retries}): {reason}",
            actor=requesting_owner_id or "user",
        )

        logger.info("Task retried", extra={"task_id": saved.id, "retry_count": saved.retry_count})
        return saved

    # Dependencies & Readiness
    def add_dependency(
        self,
        source_task_id: str,
        target_task_id: str,
        dependency_type: DependencyType = DependencyType.DEPENDS_ON,
        requesting_owner_id: str | None = None,
    ) -> TaskDependency:
        """Add dependency link between tasks (source depends on target)."""
        source_task = self.get_task(source_task_id, requesting_owner_id)
        target_task = self.get_task(target_task_id, requesting_owner_id)

        # Check cycle
        def get_outgoing(tid: str) -> list[str]:
            deps = self.dep_repo.get_dependencies_for_task(tid)
            return [d.target_task_id for d in deps if d.dependency_type in (DependencyType.DEPENDS_ON, DependencyType.BLOCKS)]

        TaskValidator.detect_dependency_cycle(source_task_id, target_task_id, get_outgoing)

        dep = TaskDependency(
            source_task_id=source_task_id,
            target_task_id=target_task_id,
            dependency_type=dependency_type,
        )
        saved_dep = self.dep_repo.save(dep)

        # Update source task readiness if blocked
        if target_task.status != TaskStatus.COMPLETED and source_task.status in (TaskStatus.READY, TaskStatus.PENDING):
            self.transition_task_status(source_task_id, TaskStatus.BLOCKED, reason=f"Blocked by task '{target_task_id}'")

        return saved_dep

    def remove_dependency(self, dependency_id: str, requesting_owner_id: str | None = None) -> bool:
        """Remove a task dependency link by ID."""
        dep = self.dep_repo.get_by_id(dependency_id)
        if not dep:
            return False

        if requesting_owner_id:
            self.get_task(dep.source_task_id, requesting_owner_id)

        deleted = self.dep_repo.delete(dependency_id)
        if deleted:
            # Re-evaluate readiness of source task
            self._evaluate_task_readiness(dep.source_task_id)
        return deleted

    def get_task_dependencies(
        self, task_id: str, requesting_owner_id: str | None = None
    ) -> tuple[list[TaskDependency], list[TaskDependency]]:
        """Get (incoming_dependencies, outgoing_dependents) for task."""
        self.get_task(task_id, requesting_owner_id)
        incoming = self.dep_repo.get_dependencies_for_task(task_id)
        outgoing = self.dep_repo.get_dependents_for_task(task_id)
        return incoming, outgoing

    def calculate_readiness(self, task_id: str) -> TaskReadinessStatus:
        """Calculate current readiness status of a task."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return TaskReadinessStatus.INVALID

        if task.status == TaskStatus.COMPLETED:
            return TaskReadinessStatus.COMPLETED
        if task.status in (TaskStatus.CANCELLED, TaskStatus.EXPIRED, TaskStatus.SKIPPED):
            return TaskReadinessStatus.CANCELLED

        incoming = self.dep_repo.get_dependencies_for_task(task_id)
        blocking = [
            d for d in incoming if d.dependency_type in (DependencyType.DEPENDS_ON, DependencyType.BLOCKS)
        ]

        for dep in blocking:
            target = self.task_repo.get_by_id(dep.target_task_id)
            if not target or target.status != TaskStatus.COMPLETED:
                return TaskReadinessStatus.BLOCKED

        return TaskReadinessStatus.READY

    # Task Groups
    def create_task_group(
        self, owner_id: str, name: str, description: str = "", metadata: dict[str, Any] | None = None
    ) -> TaskGroup:
        """Create a new TaskGroup."""
        group = TaskGroup(
            owner_id=owner_id,
            name=name,
            description=description,
            status=TaskGroupStatus.ACTIVE,
            metadata=metadata or {},
        )
        saved = self.group_repo.save(group)
        logger.info("Task group created", extra={"group_id": saved.group_id, "group_name": saved.name, "owner_id": owner_id})
        return saved

    def get_task_group(self, group_id: str, requesting_owner_id: str | None = None) -> TaskGroup:
        """Retrieve a TaskGroup by ID."""
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise TaskGroupNotFoundError(group_id)
        if requesting_owner_id and group.owner_id != requesting_owner_id:
            raise TaskGroupOwnershipError(group_id, group.owner_id, requesting_owner_id)
        return group

    def update_task_group(
        self,
        group_id: str,
        name: str | None = None,
        description: str | None = None,
        status: TaskGroupStatus | None = None,
        requesting_owner_id: str | None = None,
    ) -> TaskGroup:
        """Update TaskGroup properties."""
        group = self.get_task_group(group_id, requesting_owner_id)
        updated_dict = group.model_dump()
        if name is not None:
            updated_dict["name"] = name
        if description is not None:
            updated_dict["description"] = description
        if status is not None:
            updated_dict["status"] = status

        updated_dict["updated_at"] = datetime.utcnow()
        new_group = TaskGroup(**updated_dict)
        return self.group_repo.save(new_group)

    def delete_task_group(self, group_id: str, requesting_owner_id: str | None = None) -> bool:
        """Delete task group and unassign group_id from member tasks."""
        self.get_task_group(group_id, requesting_owner_id)
        member_tasks, _ = self.task_repo.list_tasks(group_id=group_id, limit=500)
        for task in member_tasks:
            updated_dict = task.model_dump()
            updated_dict["group_id"] = None
            self.task_repo.save(Task(**updated_dict))

        return self.group_repo.delete(group_id)

    def list_task_groups(
        self, owner_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> tuple[list[TaskGroup], int]:
        """List task groups."""
        effective_limit = min(limit, self.settings.max_page_size)
        return self.group_repo.list_groups(owner_id=owner_id, limit=effective_limit, offset=offset)

    def get_task_group_summary(self, group_id: str, requesting_owner_id: str | None = None) -> TaskGroupSummary:
        """Calculate progress summary statistics for a task group."""
        group = self.get_task_group(group_id, requesting_owner_id)
        tasks, _ = self.task_repo.list_tasks(group_id=group_id, limit=1000)

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        pending = sum(1 for t in tasks if t.status in (TaskStatus.PENDING, TaskStatus.READY))
        blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)

        total_progress = sum(t.progress for t in tasks)
        overall_progress = round(total_progress / total, 2) if total > 0 else 0.0

        return TaskGroupSummary(
            group_id=group.group_id,
            name=group.name,
            total_tasks=total,
            completed_tasks=completed,
            pending_tasks=pending,
            blocked_tasks=blocked,
            in_progress_tasks=in_progress,
            overall_progress=overall_progress,
        )

    # Plan-to-Task Conversion Integration
    def generate_tasks_from_plan(
        self, plan: Plan, owner_id: str | None = None
    ) -> tuple[list[Task], list[TaskDependency]]:
        """Convert Module 11 Reasoning Plan into Tasks and dependencies idempotently."""
        effective_owner = owner_id or plan.owner_id
        existing_tasks, _ = self.task_repo.list_tasks(plan_id=plan.plan_id, limit=500)

        generated_tasks, generated_deps = PlanTaskMapper.map_plan_to_tasks(
            plan=plan,
            owner_id=effective_owner,
            existing_tasks=existing_tasks,
        )

        saved_tasks: list[Task] = []
        for task in generated_tasks:
            saved = self.task_repo.save(task)
            saved_tasks.append(saved)
            self._record_history(
                task_id=saved.id,
                previous_status=None,
                new_status=saved.status,
                reason=f"Generated from plan '{plan.plan_id}' step '{saved.plan_step_id}'",
                actor="plan_mapper",
            )

        saved_deps: list[TaskDependency] = []
        for dep in generated_deps:
            saved_dep = self.dep_repo.save(dep)
            saved_deps.append(saved_dep)


        logger.info(
            "Tasks generated from plan",
            extra={
                "plan_id": plan.plan_id,
                "plan_version": plan.version,
                "task_count": len(saved_tasks),
                "dependency_count": len(saved_deps),
            },
        )
        return saved_tasks, saved_deps

    def get_task_history(
        self, task_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[TaskHistoryEntry], int]:
        """Retrieve audit log history for a task."""
        self.get_task(task_id)
        effective_limit = min(limit, self.settings.max_page_size)
        return self.history_repo.get_history_for_task(task_id, limit=effective_limit, offset=offset)

    # Private Internal Helpers
    def _record_history(
        self,
        task_id: str,
        previous_status: TaskStatus | None,
        new_status: TaskStatus,
        reason: str,
        actor: str = "system",
        details: dict[str, Any] | None = None,
    ) -> None:
        entry = TaskHistoryEntry(
            task_id=task_id,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            actor=actor,
            details=details or {},
        )
        self.history_repo.save_entry(entry)

    def _cancel_child_tasks(self, parent_task_id: str, actor: str) -> None:
        children, _ = self.task_repo.list_tasks(parent_task_id=parent_task_id, limit=200)
        for child in children:
            if child.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.SKIPPED):
                self.transition_task_status(
                    task_id=child.id,
                    target_status=TaskStatus.CANCELLED,
                    reason=f"Parent task '{parent_task_id}' was cancelled",
                    actor=actor,
                )

    def _evaluate_dependents_readiness(self, completed_task_id: str) -> None:
        dependents = self.dep_repo.get_dependents_for_task(completed_task_id)
        for dep in dependents:
            if dep.dependency_type in (DependencyType.DEPENDS_ON, DependencyType.BLOCKS):
                self._evaluate_task_readiness(dep.source_task_id)

    def _evaluate_task_readiness(self, task_id: str) -> None:
        task = self.task_repo.get_by_id(task_id)
        if not task or task.status not in (TaskStatus.BLOCKED, TaskStatus.PENDING):
            return

        readiness = self.calculate_readiness(task_id)
        if readiness == TaskReadinessStatus.READY:
            self.transition_task_status(
                task_id=task_id,
                target_status=TaskStatus.READY,
                reason="All blocking dependencies satisfied",
                actor="system",
            )
