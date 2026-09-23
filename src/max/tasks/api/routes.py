"""FastAPI REST API endpoints for Module 12 Task Engine."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from max.reasoning.repositories.plan_repository import InMemoryPlanRepository
from max.tasks.domain.enums import TaskPriority, TaskSource, TaskStatus, TaskType
from max.tasks.domain.exceptions import TaskError
from max.tasks.schemas.requests import (
    ConvertPlanToTasksRequest,
    CreateTaskDependencyRequest,
    CreateTaskGroupRequest,
    CreateTaskRequest,
    UpdateTaskGroupRequest,
    UpdateTaskProgressRequest,
    UpdateTaskRequest,
)
from max.tasks.schemas.responses import (
    PlanConversionResponse,
    TaskDependencyListResponse,
    TaskDependencyResponse,
    TaskGroupListResponse,
    TaskGroupResponse,
    TaskGroupSummaryResponse,
    TaskHistoryListResponse,
    TaskListResponse,
    TaskReadinessResponse,
    TaskResponse,
)
from max.tasks.services.task_service import TaskService

tasks_router = APIRouter(prefix="/tasks", tags=["Task Engine"])
task_group_router = APIRouter(prefix="/task-groups", tags=["Task Groups"])
plan_task_router = APIRouter(prefix="/plans", tags=["Plan Task Conversion"])

_task_service_instance: TaskService | None = None
_plan_repo_instance: InMemoryPlanRepository | None = None


def get_task_service() -> TaskService:
    """Dependency provider for TaskService singleton."""
    global _task_service_instance
    if _task_service_instance is None:
        _task_service_instance = TaskService()
    return _task_service_instance


def get_plan_repository() -> InMemoryPlanRepository:
    """Dependency provider for PlanRepository singleton."""
    global _plan_repo_instance
    if _plan_repo_instance is None:
        _plan_repo_instance = InMemoryPlanRepository()
    return _plan_repo_instance


def _to_task_response(task: Any) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        owner_id=task.owner_id,
        title=task.title,
        description=task.description,
        type=task.type,
        status=task.status,
        priority=task.priority,
        progress=task.progress,
        source=task.source,
        plan_id=task.plan_id,
        plan_version=task.plan_version,
        plan_step_id=task.plan_step_id,
        reasoning_id=task.reasoning_id,
        conversation_id=task.conversation_id,
        parent_task_id=task.parent_task_id,
        group_id=task.group_id,
        schedule=task.schedule,
        due_at=task.due_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        cancelled_at=task.cancelled_at,
        result=task.result,
        failure=task.failure,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
        last_retry_at=task.last_retry_at,
        retryable=task.retryable,
        references=task.references,
        metadata=task.metadata,
    )


# TASKS ENDPOINTS
@tasks_router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: CreateTaskRequest,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Create a new task record."""
    try:
        task = service.create_task(
            owner_id=payload.owner_id,
            title=payload.title,
            description=payload.description,
            type=payload.type,
            priority=payload.priority,
            source=payload.source,
            plan_id=payload.plan_id,
            plan_version=payload.plan_version,
            plan_step_id=payload.plan_step_id,
            reasoning_id=payload.reasoning_id,
            conversation_id=payload.conversation_id,
            parent_task_id=payload.parent_task_id,
            group_id=payload.group_id,
            schedule=payload.schedule,
            due_at=payload.due_at,
            references=payload.references,
            metadata=payload.metadata,
            max_retries=payload.max_retries,
        )
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.get("", response_model=TaskListResponse)
def list_tasks(
    owner_id: str | None = Query(default=None, description="Filter by owner ID"),
    group_id: str | None = Query(default=None, description="Filter by group ID"),
    plan_id: str | None = Query(default=None, description="Filter by plan ID"),
    parent_task_id: str | None = Query(default=None, description="Filter by parent task ID"),
    status: TaskStatus | None = Query(default=None, description="Filter by status"),
    priority: TaskPriority | None = Query(default=None, description="Filter by priority"),
    type: TaskType | None = Query(default=None, description="Filter by type"),
    source: TaskSource | None = Query(default=None, description="Filter by source"),
    due_before: datetime | None = Query(default=None, description="Filter due before date"),
    due_after: datetime | None = Query(default=None, description="Filter due after date"),
    search: str | None = Query(default=None, description="Title/description substring search"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    """List tasks with filtering and pagination."""
    items, total = service.list_tasks(
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
        limit=limit,
        offset=offset,
    )
    return TaskListResponse(
        items=[_to_task_response(t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@tasks_router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    owner_id: str | None = Query(default=None, description="Requesting owner ID"),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Retrieve task details by ID."""
    try:
        task = service.get_task(task_id, requesting_owner_id=owner_id)
        return _to_task_response(task)
    except TaskError as e:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@tasks_router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    payload: UpdateTaskRequest,
    owner_id: str | None = Query(default=None, description="Requesting owner ID"),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Update task properties."""
    try:
        updated = service.update_task(
            task_id=task_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            type=payload.type,
            due_at=payload.due_at,
            group_id=payload.group_id,
            parent_task_id=payload.parent_task_id,
            metadata=payload.metadata,
            requesting_owner_id=owner_id,
        )
        return _to_task_response(updated)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    owner_id: str | None = Query(default=None, description="Requesting owner ID"),
    service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task by ID."""
    try:
        service.delete_task(task_id, requesting_owner_id=owner_id)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


# LIFECYCLE TRANSITIONS
@tasks_router.post("/{task_id}/ready", response_model=TaskResponse)
def mark_task_ready(
    task_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Transition task status to READY."""
    try:
        task = service.transition_task_status(
            task_id=task_id,
            target_status=TaskStatus.READY,
            reason="Marked ready via API",
            actor=owner_id or "user",
            requesting_owner_id=owner_id,
        )
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.post("/{task_id}/start", response_model=TaskResponse)
def start_task(
    task_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Transition task status to IN_PROGRESS. DOES NOT EXECUTE ACTIVE ACTIONS."""
    try:
        task = service.start_task(task_id, requesting_owner_id=owner_id)
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.post("/{task_id}/pause", response_model=TaskResponse)
def pause_task(
    task_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Transition active task status to PAUSED."""
    try:
        task = service.pause_task(task_id, requesting_owner_id=owner_id)
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.post("/{task_id}/resume", response_model=TaskResponse)
def resume_task(
    task_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Transition paused task status back to IN_PROGRESS."""
    try:
        task = service.resume_task(task_id, requesting_owner_id=owner_id)
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    summary: str = Query(default="Task completed"),
    output_reference: str | None = Query(default=None),
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Transition task status to COMPLETED."""
    try:
        task = service.complete_task(
            task_id=task_id,
            result_summary=summary,
            output_reference=output_reference,
            requesting_owner_id=owner_id,
        )
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(
    task_id: str,
    reason: str = Query(default="Task cancelled"),
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Transition task status to CANCELLED."""
    try:
        task = service.cancel_task(task_id, reason=reason, requesting_owner_id=owner_id)
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.post("/{task_id}/retry", response_model=TaskResponse)
def retry_task(
    task_id: str,
    reason: str = Query(default="Retry requested via API"),
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Reset a FAILED task back to READY if retryable."""
    try:
        task = service.retry_task(task_id, reason=reason, requesting_owner_id=owner_id)
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.patch("/{task_id}/progress", response_model=TaskResponse)
def update_progress(
    task_id: str,
    payload: UpdateTaskProgressRequest,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Update task progress percentage (0-100)."""
    try:
        task = service.update_progress(
            task_id=task_id,
            progress=payload.progress,
            reason=payload.reason,
            requesting_owner_id=owner_id,
        )
        return _to_task_response(task)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


# DEPENDENCIES
@tasks_router.post(
    "/{task_id}/dependencies",
    response_model=TaskDependencyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dependency(
    task_id: str,
    payload: CreateTaskDependencyRequest,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskDependencyResponse:
    """Add dependency link where task_id depends on target_task_id."""
    try:
        dep = service.add_dependency(
            source_task_id=task_id,
            target_task_id=payload.target_task_id,
            dependency_type=payload.dependency_type,
            requesting_owner_id=owner_id,
        )
        return TaskDependencyResponse(
            dependency_id=dep.dependency_id,
            source_task_id=dep.source_task_id,
            target_task_id=dep.target_task_id,
            dependency_type=dep.dependency_type,
            created_at=dep.created_at,
        )
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.get("/{task_id}/dependencies", response_model=TaskDependencyListResponse)
def list_dependencies(
    task_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskDependencyListResponse:
    """List incoming dependencies and outgoing dependents for a task."""
    try:
        incoming, outgoing = service.get_task_dependencies(task_id, requesting_owner_id=owner_id)
        return TaskDependencyListResponse(
            incoming_dependencies=[
                TaskDependencyResponse(
                    dependency_id=d.dependency_id,
                    source_task_id=d.source_task_id,
                    target_task_id=d.target_task_id,
                    dependency_type=d.dependency_type,
                    created_at=d.created_at,
                )
                for d in incoming
            ],
            outgoing_dependents=[
                TaskDependencyResponse(
                    dependency_id=d.dependency_id,
                    source_task_id=d.source_task_id,
                    target_task_id=d.target_task_id,
                    dependency_type=d.dependency_type,
                    created_at=d.created_at,
                )
                for d in outgoing
            ],
        )
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.delete(
    "/{task_id}/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_dependency(
    task_id: str,
    dependency_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> None:
    """Remove a task dependency relationship."""
    try:
        service.remove_dependency(dependency_id, requesting_owner_id=owner_id)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@tasks_router.get("/{task_id}/readiness", response_model=TaskReadinessResponse)
def get_task_readiness(
    task_id: str,
    service: TaskService = Depends(get_task_service),
) -> TaskReadinessResponse:
    """Evaluate task readiness based on status and blocking dependencies."""
    task = service.get_task(task_id)
    readiness = service.calculate_readiness(task_id)
    return TaskReadinessResponse(
        task_id=task_id,
        readiness_status=readiness,
        current_status=task.status,
    )


@tasks_router.get("/{task_id}/history", response_model=TaskHistoryListResponse)
def get_task_history(
    task_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(get_task_service),
) -> TaskHistoryListResponse:
    """Retrieve audit history log for a task."""
    try:
        items, total = service.get_task_history(task_id, limit=limit, offset=offset)
        return TaskHistoryListResponse(items=items, total=total, limit=limit, offset=offset)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


# TASK GROUPS ENDPOINTS
@task_group_router.post("", response_model=TaskGroupResponse, status_code=status.HTTP_201_CREATED)
def create_task_group(
    payload: CreateTaskGroupRequest,
    service: TaskService = Depends(get_task_service),
) -> TaskGroupResponse:
    """Create a new task group."""
    try:
        group = service.create_task_group(
            owner_id=payload.owner_id,
            name=payload.name,
            description=payload.description,
            metadata=payload.metadata,
        )
        return TaskGroupResponse(
            group_id=group.group_id,
            owner_id=group.owner_id,
            name=group.name,
            description=group.description,
            status=group.status,
            created_at=group.created_at,
            updated_at=group.updated_at,
            metadata=group.metadata,
        )
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@task_group_router.get("", response_model=TaskGroupListResponse)
def list_task_groups(
    owner_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(get_task_service),
) -> TaskGroupListResponse:
    """List task groups with pagination."""
    groups, total = service.list_task_groups(owner_id=owner_id, limit=limit, offset=offset)
    return TaskGroupListResponse(
        items=[
            TaskGroupResponse(
                group_id=g.group_id,
                owner_id=g.owner_id,
                name=g.name,
                description=g.description,
                status=g.status,
                created_at=g.created_at,
                updated_at=g.updated_at,
                metadata=g.metadata,
            )
            for g in groups
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@task_group_router.get("/{group_id}", response_model=TaskGroupResponse)
def get_task_group(
    group_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskGroupResponse:
    """Retrieve task group details by ID."""
    try:
        group = service.get_task_group(group_id, requesting_owner_id=owner_id)
        return TaskGroupResponse(
            group_id=group.group_id,
            owner_id=group.owner_id,
            name=group.name,
            description=group.description,
            status=group.status,
            created_at=group.created_at,
            updated_at=group.updated_at,
            metadata=group.metadata,
        )
    except TaskError as e:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@task_group_router.get("/{group_id}/summary", response_model=TaskGroupSummaryResponse)
def get_task_group_summary(
    group_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskGroupSummaryResponse:
    """Calculate progress summary statistics for a task group."""
    try:
        summary = service.get_task_group_summary(group_id, requesting_owner_id=owner_id)
        return TaskGroupSummaryResponse(
            group_id=summary.group_id,
            name=summary.name,
            total_tasks=summary.total_tasks,
            completed_tasks=summary.completed_tasks,
            pending_tasks=summary.pending_tasks,
            blocked_tasks=summary.blocked_tasks,
            in_progress_tasks=summary.in_progress_tasks,
            overall_progress=summary.overall_progress,
        )
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@task_group_router.patch("/{group_id}", response_model=TaskGroupResponse)
def update_task_group(
    group_id: str,
    payload: UpdateTaskGroupRequest,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> TaskGroupResponse:
    """Update task group attributes."""
    try:
        group = service.update_task_group(
            group_id=group_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            requesting_owner_id=owner_id,
        )
        return TaskGroupResponse(
            group_id=group.group_id,
            owner_id=group.owner_id,
            name=group.name,
            description=group.description,
            status=group.status,
            created_at=group.created_at,
            updated_at=group.updated_at,
            metadata=group.metadata,
        )
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@task_group_router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_group(
    group_id: str,
    owner_id: str | None = Query(default=None),
    service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task group."""
    try:
        service.delete_task_group(group_id, requesting_owner_id=owner_id)
    except TaskError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


# PLAN TASK CONVERSION ENDPOINT
@plan_task_router.post(
    "/{plan_id}/tasks", response_model=PlanConversionResponse, status_code=status.HTTP_201_CREATED
)
async def convert_plan_to_tasks(
    plan_id: str,
    payload: ConvertPlanToTasksRequest | None = None,
    service: TaskService = Depends(get_task_service),
    plan_repo: InMemoryPlanRepository = Depends(get_plan_repository),
) -> PlanConversionResponse:
    """Convert a Module 11 Reasoning Plan into Tasks and dependencies idempotently."""
    plan = await plan_repo.get_by_id(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found."
        )

    owner_id = payload.owner_id if payload else None
    tasks, deps = service.generate_tasks_from_plan(plan=plan, owner_id=owner_id)

    return PlanConversionResponse(
        plan_id=plan.plan_id,
        plan_version=plan.version,
        generated_tasks_count=len(tasks),
        generated_dependencies_count=len(deps),
        tasks=[_to_task_response(t) for t in tasks],
    )
