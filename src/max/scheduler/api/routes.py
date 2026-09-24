"""FastAPI API routes for Module 28 — Scheduler & Automation Engine."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from max.scheduler.container import get_scheduler_container
from max.scheduler.domain.enums import AutomationStatus
from max.scheduler.domain.exceptions import (
    AutomationNotFoundError,
    AutomationValidationError,
    InvalidStateTransitionError,
    ScheduleNotFoundError,
    ScheduleValidationError,
)
from max.scheduler.domain.models import Automation, Schedule
from max.scheduler.schemas.scheduler_schemas import (
    AutomationCreateRequest,
    AutomationResponse,
    AutomationUpdateRequest,
    DryRunResponse,
    ExecutionResponse,
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
)

scheduler_router = APIRouter(prefix="/scheduler", tags=["Scheduler Engine"])
automations_router = APIRouter(prefix="/automations", tags=["Automation Engine"])


# Helpers for conversion to responses

def _schedule_to_response(sch: Schedule) -> ScheduleResponse:
    return ScheduleResponse(
        schedule_id=sch.schedule_id,
        schedule_type=sch.schedule_type,
        status=sch.status,
        owner_id=sch.owner_id,
        automation_id=sch.automation_id,
        cron_expression=sch.cron_expression,
        interval_seconds=sch.interval_seconds,
        scheduled_at=sch.scheduled_at,
        recurrence_rule=sch.recurrence_rule,
        timezone=sch.timezone,
        misfire_policy=sch.misfire_policy,
        concurrency_policy=sch.concurrency_policy,
        next_run_at=sch.next_run_at,
        last_run_at=sch.last_run_at,
        consecutive_failures=sch.consecutive_failures,
        metadata=sch.metadata,
    )


def _automation_to_response(aut: Automation) -> AutomationResponse:
    return AutomationResponse(
        automation_id=aut.automation_id,
        name=aut.name,
        description=aut.description,
        status=aut.status,
        owner_id=aut.owner_id,
        definition=aut.definition,
        version=aut.version,
        trigger=aut.trigger,
        dependencies=aut.dependencies,
        concurrency_policy=aut.concurrency_policy,
        misfire_policy=aut.misfire_policy,
        retry_policy=aut.retry_policy,
        metadata=aut.metadata,
    )


# SCHEDULER ENDPOINTS

@scheduler_router.post(
    "",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new schedule",
)
def create_schedule(request: ScheduleCreateRequest) -> ScheduleResponse:
    container = get_scheduler_container()
    sch = Schedule(**request.model_dump())
    try:
        created = container.scheduler_service.create_schedule(sch)
        return _schedule_to_response(created)
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@scheduler_router.get("", response_model=list[ScheduleResponse], summary="List schedules")
def list_schedules(
    owner_id: str | None = Query(None, description="Filter by owner ID"),
    status: str | None = Query(None, description="Filter by status"),
    schedule_type: str | None = Query(None, description="Filter by type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[ScheduleResponse]:
    container = get_scheduler_container()
    schedules = container.scheduler_service.schedule_repo.list(
        owner_id=owner_id, status=status, schedule_type=schedule_type, limit=limit, offset=offset
    )
    return [_schedule_to_response(s) for s in schedules]


@scheduler_router.get(
    "/executions",
    response_model=list[ExecutionResponse],
    summary="List execution history across schedules",
)
def list_executions(
    automation_id: str | None = Query(None),
    schedule_id: str | None = Query(None),
    owner_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[ExecutionResponse]:
    container = get_scheduler_container()
    execs = container.scheduler_service.execution_repo.list(
        automation_id=automation_id,
        schedule_id=schedule_id,
        owner_id=owner_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [ExecutionResponse(**e.model_dump()) for e in execs]


@scheduler_router.get(
    "/{schedule_id}", response_model=ScheduleResponse, summary="Get schedule by ID"
)
def get_schedule(schedule_id: str) -> ScheduleResponse:
    container = get_scheduler_container()
    sch = container.scheduler_service.schedule_repo.get_by_id(schedule_id)
    if not sch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found."
        )
    return _schedule_to_response(sch)


@scheduler_router.put(
    "/{schedule_id}", response_model=ScheduleResponse, summary="Update schedule"
)
def update_schedule(schedule_id: str, request: ScheduleUpdateRequest) -> ScheduleResponse:
    container = get_scheduler_container()
    existing = container.scheduler_service.schedule_repo.get_by_id(schedule_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found."
        )

    patch = request.model_dump(exclude_unset=True)
    for k, v in patch.items():
        setattr(existing, k, v)

    try:
        updated = container.scheduler_service.update_schedule(existing)
        return _schedule_to_response(updated)
    except ScheduleValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@scheduler_router.post(
    "/{schedule_id}/pause", response_model=ScheduleResponse, summary="Pause a schedule"
)
def pause_schedule(schedule_id: str) -> ScheduleResponse:
    container = get_scheduler_container()
    try:
        sch = container.scheduler_service.pause_schedule(schedule_id)
        return _schedule_to_response(sch)
    except ScheduleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found."
        ) from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc


@scheduler_router.post(
    "/{schedule_id}/resume", response_model=ScheduleResponse, summary="Resume a paused schedule"
)
def resume_schedule(schedule_id: str) -> ScheduleResponse:
    container = get_scheduler_container()
    try:
        sch = container.scheduler_service.resume_schedule(schedule_id)
        return _schedule_to_response(sch)
    except ScheduleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found."
        ) from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc


@scheduler_router.post(
    "/{schedule_id}/cancel", response_model=ScheduleResponse, summary="Cancel a schedule"
)
def cancel_schedule(schedule_id: str) -> ScheduleResponse:
    container = get_scheduler_container()
    try:
        sch = container.scheduler_service.cancel_schedule(schedule_id)
        return _schedule_to_response(sch)
    except ScheduleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found."
        ) from exc


@scheduler_router.delete("/{schedule_id}", summary="Delete a schedule")
def delete_schedule(schedule_id: str) -> dict[str, str]:
    container = get_scheduler_container()
    deleted = container.scheduler_service.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found."
        )
    return {"message": f"Schedule '{schedule_id}' deleted successfully."}


@scheduler_router.post(
    "/{schedule_id}/trigger", response_model=ExecutionResponse, summary="Manually trigger schedule"
)
def trigger_schedule(schedule_id: str) -> ExecutionResponse:
    container = get_scheduler_container()
    sch = container.scheduler_service.schedule_repo.get_by_id(schedule_id)
    if not sch or not sch.automation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule '{schedule_id}' not found or lacks automation.",
        )

    exc = container.scheduler_service.trigger_manually(
        automation_id=sch.automation_id, owner_id=sch.owner_id
    )
    return ExecutionResponse(**exc.model_dump())


@scheduler_router.get("/{schedule_id}/next-run", summary="Get next run timestamp")
def get_next_run(schedule_id: str) -> dict[str, Any]:
    container = get_scheduler_container()
    try:
        next_run = container.scheduler_service.get_next_run(schedule_id)
        return {"schedule_id": schedule_id, "next_run_at": next_run}
    except ScheduleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found."
        ) from exc


@scheduler_router.get("/{schedule_id}/status", summary="Get schedule status")
def get_schedule_status(schedule_id: str) -> dict[str, Any]:
    container = get_scheduler_container()
    sch = container.scheduler_service.schedule_repo.get_by_id(schedule_id)
    if not sch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule '{schedule_id}' not found."
        )
    return {"schedule_id": schedule_id, "status": sch.status.value, "next_run_at": sch.next_run_at}


# AUTOMATIONS ENDPOINTS

@automations_router.post(
    "",
    response_model=AutomationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an automation",
)
def create_automation(request: AutomationCreateRequest) -> AutomationResponse:
    container = get_scheduler_container()
    aut = Automation(**request.model_dump())
    try:
        created = container.automation_engine.create_automation(aut)
        return _automation_to_response(created)
    except AutomationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@automations_router.get("", response_model=list[AutomationResponse], summary="List automations")
def list_automations(
    owner_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[AutomationResponse]:
    container = get_scheduler_container()
    automations = container.automation_engine.automation_repo.list(
        owner_id=owner_id, status=status, limit=limit, offset=offset
    )
    return [_automation_to_response(a) for a in automations]


@automations_router.get(
    "/{automation_id}", response_model=AutomationResponse, summary="Get automation by ID"
)
def get_automation(automation_id: str) -> AutomationResponse:
    container = get_scheduler_container()
    aut = container.automation_engine.automation_repo.get_by_id(automation_id)
    if not aut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Automation '{automation_id}' not found."
        )
    return _automation_to_response(aut)


@automations_router.put(
    "/{automation_id}", response_model=AutomationResponse, summary="Update automation"
)
def update_automation(automation_id: str, request: AutomationUpdateRequest) -> AutomationResponse:
    container = get_scheduler_container()
    existing = container.automation_engine.automation_repo.get_by_id(automation_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Automation '{automation_id}' not found."
        )

    patch = request.model_dump(exclude_unset=True)
    for k, v in patch.items():
        setattr(existing, k, v)

    try:
        updated = container.automation_engine.update_automation(existing)
        return _automation_to_response(updated)
    except (AutomationValidationError, AutomationNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@automations_router.post(
    "/{automation_id}/enable", response_model=AutomationResponse, summary="Enable an automation"
)
def enable_automation(automation_id: str) -> AutomationResponse:
    container = get_scheduler_container()
    aut = container.automation_engine.automation_repo.get_by_id(automation_id)
    if not aut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Automation '{automation_id}' not found."
        )

    aut.status = AutomationStatus.SCHEDULED
    container.automation_engine.automation_repo.save(aut)
    return _automation_to_response(aut)


@automations_router.post(
    "/{automation_id}/disable", response_model=AutomationResponse, summary="Disable an automation"
)
def disable_automation(automation_id: str) -> AutomationResponse:
    container = get_scheduler_container()
    aut = container.automation_engine.automation_repo.get_by_id(automation_id)
    if not aut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Automation '{automation_id}' not found."
        )

    aut.status = AutomationStatus.DISABLED
    container.automation_engine.automation_repo.save(aut)
    return _automation_to_response(aut)


@automations_router.post(
    "/{automation_id}/trigger", response_model=ExecutionResponse, summary="Trigger automation"
)
def trigger_automation(automation_id: str) -> ExecutionResponse:
    container = get_scheduler_container()
    try:
        exc = container.automation_engine.execute_automation(automation_id=automation_id)
        return ExecutionResponse(**exc.model_dump())
    except AutomationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Automation '{automation_id}' not found."
        ) from exc


@automations_router.post(
    "/{automation_id}/dry-run", response_model=DryRunResponse, summary="Dry-run automation"
)
def dry_run_automation(automation_id: str) -> DryRunResponse:
    container = get_scheduler_container()
    try:
        exc = container.automation_engine.execute_automation(
            automation_id=automation_id, dry_run=True
        )
        plan = exc.result.get("plan", {})
        return DryRunResponse(
            automation_id=automation_id,
            version=exc.automation_version,
            total_steps=plan.get("total_steps", 0),
            steps=plan.get("steps", []),
        )
    except AutomationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Automation '{automation_id}' not found."
        ) from exc


@automations_router.get(
    "/{automation_id}/executions",
    response_model=list[ExecutionResponse],
    summary="Get automation executions",
)
def list_automation_executions(
    automation_id: str, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)
) -> list[ExecutionResponse]:
    container = get_scheduler_container()
    execs = container.scheduler_service.execution_repo.list(
        automation_id=automation_id, limit=limit, offset=offset
    )
    return [ExecutionResponse(**e.model_dump()) for e in execs]


@automations_router.get("/{automation_id}/status", summary="Get automation status")
def get_automation_status(automation_id: str) -> dict[str, Any]:
    container = get_scheduler_container()
    aut = container.automation_engine.automation_repo.get_by_id(automation_id)
    if not aut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Automation '{automation_id}' not found."
        )
    return {
        "automation_id": automation_id,
        "status": aut.status.value,
        "version": aut.version,
    }
