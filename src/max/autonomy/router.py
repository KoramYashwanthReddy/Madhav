"""FastAPI Router for Module 41 — Future Autonomous Intelligence endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field

from max.autonomy.domain import (
    ApprovalRequest,
    AutonomyHealth,
    AutonomyLevel,
    AutonomyPolicy,
    Mission,
    MissionAction,
    MissionResult,
    ResourceBudget,
)
from max.autonomy.service import AutonomyService, get_autonomy_service
from max.core.request_id import get_request_id
from max.core.responses import APIResponse

router = APIRouter(prefix="/autonomy", tags=["Future Autonomous Intelligence"])


class CreateMissionRequest(BaseModel):
    """Payload for creating a new mission."""

    title: str = Field(..., description="Mission title")
    objective: str = Field(..., description="High-level objective")
    autonomy_level: AutonomyLevel = Field(default=AutonomyLevel.SUPERVISED, description="Autonomy level")
    allowed_scope: list[str] | None = Field(default=None, description="Allowed resource paths/domains")
    budget: ResourceBudget | None = Field(default=None, description="Resource budget constraints")
    actions: list[MissionAction] | None = Field(default=None, description="Initial step list")


class KillSwitchRequest(BaseModel):
    """Payload for setting the emergency kill-switch."""

    active: bool = Field(..., description="Enable or disable emergency autonomy kill-switch")


class UpdatePolicyRequest(BaseModel):
    """Payload for updating governance policy parameters."""

    level: str | None = Field(default=None, description="Autonomy level (MANUAL..HIGH_AUTONOMY)")
    allowed_actions: list[str] | None = Field(default=None, description="Allowed action patterns")
    blocked_actions: list[str] | None = Field(default=None, description="Blocked action patterns")
    require_approval_risk: str | None = Field(default=None, description="Min risk level requiring approval")


@router.get("/status", response_model=APIResponse[dict[str, Any]])
async def get_autonomy_status(
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[dict[str, Any]]:
    """Retrieve diagnostic overview status for Module 41 Autonomy."""
    health = svc.get_health()
    policy = svc.get_policy()

    return APIResponse(
        success=True,
        data={
            "module": "Module 41 — Future Autonomous Intelligence",
            "autonomy_level": policy.level.value,
            "kill_switch_active": health.kill_switch_active,
            "active_missions": health.active_missions,
            "pending_approvals": health.pending_approvals,
            "health": health.model_dump(),
        },
        request_id=get_request_id(),
    )


@router.get("/policy", response_model=APIResponse[AutonomyPolicy])
async def get_policy(
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[AutonomyPolicy]:
    """Retrieve global governance policy configuration."""
    return APIResponse(
        success=True,
        data=svc.get_policy(),
        request_id=get_request_id(),
    )


@router.put("/policy", response_model=APIResponse[AutonomyPolicy])
async def update_policy(
    req: UpdatePolicyRequest,
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[AutonomyPolicy]:
    """Update global governance policy parameters."""
    updates = req.model_dump(exclude_none=True)
    updated = svc.update_policy(updates)
    return APIResponse(
        success=True,
        data=updated,
        request_id=get_request_id(),
    )


@router.post("/kill-switch", response_model=APIResponse[dict[str, Any]])
async def set_kill_switch(
    req: KillSwitchRequest,
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[dict[str, Any]]:
    """Activate or deactivate global emergency autonomy kill-switch."""
    active = svc.set_kill_switch(req.active)
    return APIResponse(
        success=True,
        data={"kill_switch_active": active, "message": f"Global kill switch set to {active}."},
        request_id=get_request_id(),
    )


@router.get("/missions", response_model=APIResponse[list[Mission]])
async def list_missions(
    status: str | None = Query(default=None, description="Filter by mission status"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[list[Mission]]:
    """List registered missions."""
    missions = svc.list_missions(status=status)
    return APIResponse(
        success=True,
        data=missions,
        request_id=get_request_id(),
    )


@router.post("/missions", response_model=APIResponse[Mission], status_code=201)
async def create_mission(
    req: CreateMissionRequest,
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[Mission]:
    """Create new autonomous mission."""
    mission = svc.create_mission(
        title=req.title,
        objective=req.objective,
        autonomy_level=req.autonomy_level,
        allowed_scope=req.allowed_scope,
        budget=req.budget,
        actions=req.actions,
    )
    return APIResponse(
        success=True,
        data=mission,
        request_id=get_request_id(),
    )


@router.get("/missions/{mission_id}", response_model=APIResponse[Mission])
async def get_mission(
    mission_id: str = Path(..., description="Target mission ID"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[Mission]:
    """Retrieve details for a specific mission."""
    mission = svc.get_mission(mission_id)
    return APIResponse(
        success=True,
        data=mission,
        request_id=get_request_id(),
    )


@router.post("/missions/{mission_id}/start", response_model=APIResponse[MissionResult])
async def start_mission(
    mission_id: str = Path(..., description="Target mission ID"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[MissionResult]:
    """Execute autonomous mission execution loop."""
    result = svc.run_mission(mission_id)
    return APIResponse(
        success=result.verification_passed,
        data=result,
        request_id=get_request_id(),
    )


@router.post("/missions/{mission_id}/pause", response_model=APIResponse[Mission])
async def pause_mission(
    mission_id: str = Path(..., description="Target mission ID"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[Mission]:
    """Pause a running mission."""
    paused = svc.pause_mission(mission_id)
    return APIResponse(
        success=True,
        data=paused,
        request_id=get_request_id(),
    )


@router.post("/missions/{mission_id}/resume", response_model=APIResponse[MissionResult])
async def resume_mission(
    mission_id: str = Path(..., description="Target mission ID"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[MissionResult]:
    """Resume execution of a paused mission."""
    result = svc.resume_mission(mission_id)
    return APIResponse(
        success=result.verification_passed,
        data=result,
        request_id=get_request_id(),
    )


@router.post("/missions/{mission_id}/cancel", response_model=APIResponse[Mission])
async def cancel_mission(
    mission_id: str = Path(..., description="Target mission ID"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[Mission]:
    """Cancel a mission."""
    cancelled = svc.cancel_mission(mission_id)
    return APIResponse(
        success=True,
        data=cancelled,
        request_id=get_request_id(),
    )


@router.post("/missions/{mission_id}/dry-run", response_model=APIResponse[dict[str, Any]])
async def dry_run_mission(
    mission_id: str = Path(..., description="Target mission ID"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[dict[str, Any]]:
    """Perform pre-flight dry-run simulation of planned mission actions."""
    res = svc.dry_run_mission(mission_id)
    return APIResponse(
        success=True,
        data=res,
        request_id=get_request_id(),
    )


@router.get("/approvals", response_model=APIResponse[list[ApprovalRequest]])
async def list_pending_approvals(
    mission_id: str | None = Query(default=None, description="Optional mission ID filter"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[list[ApprovalRequest]]:
    """List pending human approval requests."""
    pending = svc.list_pending_approvals(mission_id)
    return APIResponse(
        success=True,
        data=pending,
        request_id=get_request_id(),
    )


@router.post("/approvals/{approval_id}/approve", response_model=APIResponse[ApprovalRequest])
async def approve_request(
    approval_id: str = Path(..., description="Approval request ID"),
    user_id: str = Query(default="user_admin", description="Approving admin user ID"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[ApprovalRequest]:
    """Approve a pending action request."""
    approved = svc.approve_request(approval_id, user_id)
    return APIResponse(
        success=True,
        data=approved,
        request_id=get_request_id(),
    )


@router.post("/approvals/{approval_id}/deny", response_model=APIResponse[ApprovalRequest])
async def deny_request(
    approval_id: str = Path(..., description="Approval request ID"),
    user_id: str = Query(default="user_admin", description="Denying admin user ID"),
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[ApprovalRequest]:
    """Deny a pending action request."""
    denied = svc.deny_request(approval_id, user_id)
    return APIResponse(
        success=True,
        data=denied,
        request_id=get_request_id(),
    )


@router.get("/health", response_model=APIResponse[AutonomyHealth])
async def get_health(
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[AutonomyHealth]:
    """Retrieve telemetry diagnostic metrics."""
    return APIResponse(
        success=True,
        data=svc.get_health(),
        request_id=get_request_id(),
    )


@router.post("/safety-tests", response_model=APIResponse[dict[str, Any]])
async def run_safety_tests(
    svc: AutonomyService = Depends(get_autonomy_service),
) -> APIResponse[dict[str, Any]]:
    """Execute automated safety and compliance test suite."""
    res = svc.run_safety_tests()
    return APIResponse(
        success=res["all_tests_passed"],
        data=res,
        request_id=get_request_id(),
    )
