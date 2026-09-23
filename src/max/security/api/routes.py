"""FastAPI REST API routes for Module 15 — Permission & Security."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from max.core.exceptions import NotFoundError
from max.security.container import SecurityContainer, get_security_container
from max.security.domain.approval import ApprovalDecision
from max.security.domain.decision import PermissionRequest
from max.security.domain.enums import (
    ApprovalStatus,
    SecurityEventType,
    SecurityViolationType,
)
from max.security.domain.exceptions import (
    ApprovalNotFoundError,
    InvalidApprovalError,
    InvalidPolicyError,
    PermissionExpiredError,
    SecurityError,
)
from max.security.domain.permission import PermissionCondition, PermissionRule
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject
from max.security.schemas.requests import (
    EmergencyBlockRequest,
    PermissionCheckRequest,
    PermissionGrantRequest,
    PolicyCreateRequest,
    PolicyUpdateRequest,
    SecurityModeRequest,
)
from max.security.schemas.responses import (
    ApprovalRequestResponse,
    EmergencyBlockResponse,
    PaginatedSecurityResponse,
    PermissionDecisionResponse,
    PermissionGrantResponse,
    PolicyResponse,
    SecurityEventResponse,
    SecurityModeResponse,
    SecurityViolationResponse,
)

router = APIRouter(prefix="/security", tags=["Permission & Security"])


def get_container() -> SecurityContainer:
    return get_security_container()


# ---------------------------------------------------------
# Permission Check / Gate Endpoints
# ---------------------------------------------------------


@router.post(
    "/permissions/check",
    response_model=PermissionDecisionResponse,
    summary="Evaluate permission for a requested action",
)
def check_permission(
    payload: PermissionCheckRequest,
    container: SecurityContainer = Depends(get_container),
) -> PermissionDecisionResponse:
    """Evaluate permission for an action request and return structured decision."""
    try:
        subject = PermissionSubject(
            subject_type=payload.subject.subject_type,
            subject_id=payload.subject.subject_id,
            name=payload.subject.name,
        )
        resource = PermissionResource(
            resource_type=payload.resource.resource_type,
            resource_id=payload.resource.resource_id,
            location=payload.resource.location,
            owner_id=payload.resource.owner_id,
            sensitivity=payload.resource.sensitivity,
        )
        request = PermissionRequest(
            subject=subject,
            tool_reference=payload.tool_reference,
            action=payload.action,
            resource=resource,
            owner_id=payload.owner_id,
            agent_id=payload.agent_id,
            agent_run_id=payload.agent_run_id,
            task_id=payload.task_id,
            plan_id=payload.plan_id,
            conversation_id=payload.conversation_id,
            risk_level=payload.risk_level,
            arguments=payload.arguments,
        )

        decision, token = container.gate.check_and_authorize(request)
        return PermissionDecisionResponse.from_domain(decision, token)
    except SecurityError as err:
        raise HTTPException(status_code=err.status_code, detail=err.message) from err


# ---------------------------------------------------------
# Policy Management Endpoints
# ---------------------------------------------------------


@router.post(
    "/policies",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new permission policy",
)
def create_policy(
    payload: PolicyCreateRequest,
    container: SecurityContainer = Depends(get_container),
) -> PolicyResponse:
    try:
        rules = [
            PermissionRule(
                effect=r.effect,
                priority=r.priority,
                reason=r.reason,
                subject_conditions=[
                    PermissionCondition(**c.model_dump()) for c in r.subject_conditions
                ],
                action_conditions=[
                    PermissionCondition(**c.model_dump()) for c in r.action_conditions
                ],
                resource_conditions=[
                    PermissionCondition(**c.model_dump()) for c in r.resource_conditions
                ],
                tool_conditions=[PermissionCondition(**c.model_dump()) for c in r.tool_conditions],
                time_conditions=[PermissionCondition(**c.model_dump()) for c in r.time_conditions],
            )
            for r in payload.rules
        ]

        policy = container.policy_service.create_policy(
            name=payload.name,
            owner_id=payload.owner_id,
            description=payload.description,
            priority=payload.priority,
            enabled=payload.enabled,
            rules=rules,
            scope=payload.scope,
        )
        return PolicyResponse.from_domain(policy)
    except InvalidPolicyError as err:
        raise HTTPException(status_code=400, detail=err.message) from err


@router.get(
    "/policies",
    response_model=PaginatedSecurityResponse,
    summary="List permission policies",
)
def list_policies(
    owner_id: str | None = Query(default=None, description="Filter by owner ID"),
    enabled_only: bool = Query(default=False, description="List enabled policies only"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    container: SecurityContainer = Depends(get_container),
) -> PaginatedSecurityResponse:
    policies, total = container.policy_service.list_policies(
        owner_id=owner_id,
        enabled_only=enabled_only,
        limit=limit,
        offset=offset,
    )
    items = [PolicyResponse.from_domain(p) for p in policies]
    return PaginatedSecurityResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyResponse,
    summary="Get policy by ID",
)
def get_policy(
    policy_id: str,
    container: SecurityContainer = Depends(get_container),
) -> PolicyResponse:
    try:
        policy = container.policy_service.get_policy(policy_id)
        return PolicyResponse.from_domain(policy)
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=err.message) from err


@router.patch(
    "/policies/{policy_id}",
    response_model=PolicyResponse,
    summary="Update policy by ID",
)
def update_policy(
    policy_id: str,
    payload: PolicyUpdateRequest,
    container: SecurityContainer = Depends(get_container),
) -> PolicyResponse:
    try:
        rules = None
        if payload.rules is not None:
            rules = [
                PermissionRule(
                    effect=r.effect,
                    priority=r.priority,
                    reason=r.reason,
                    subject_conditions=[
                        PermissionCondition(**c.model_dump()) for c in r.subject_conditions
                    ],
                    action_conditions=[
                        PermissionCondition(**c.model_dump()) for c in r.action_conditions
                    ],
                    resource_conditions=[
                        PermissionCondition(**c.model_dump()) for c in r.resource_conditions
                    ],
                    tool_conditions=[
                        PermissionCondition(**c.model_dump()) for c in r.tool_conditions
                    ],
                    time_conditions=[
                        PermissionCondition(**c.model_dump()) for c in r.time_conditions
                    ],
                )
                for r in payload.rules
            ]

        updated = container.policy_service.update_policy(
            policy_id=policy_id,
            name=payload.name,
            description=payload.description,
            priority=payload.priority,
            enabled=payload.enabled,
            rules=rules,
        )
        return PolicyResponse.from_domain(updated)
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=err.message) from err


@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete policy by ID",
)
def delete_policy(
    policy_id: str,
    container: SecurityContainer = Depends(get_container),
) -> None:
    try:
        container.policy_service.delete_policy(policy_id)
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=err.message) from err


# ---------------------------------------------------------
# Human Approvals Endpoints
# ---------------------------------------------------------


@router.get(
    "/approvals",
    response_model=PaginatedSecurityResponse,
    summary="List approval requests",
)
def list_approvals(
    owner_id: str | None = Query(default=None),
    status_filter: ApprovalStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    container: SecurityContainer = Depends(get_container),
) -> PaginatedSecurityResponse:
    approvals, total = container.approval_service.list_approvals(
        owner_id=owner_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    items = [ApprovalRequestResponse.from_domain(a) for a in approvals]
    return PaginatedSecurityResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/approvals/{approval_id}",
    response_model=ApprovalRequestResponse,
    summary="Get approval request by ID",
)
def get_approval(
    approval_id: str,
    container: SecurityContainer = Depends(get_container),
) -> ApprovalRequestResponse:
    try:
        approval = container.approval_service.get_approval(approval_id)
        return ApprovalRequestResponse.from_domain(approval)
    except ApprovalNotFoundError as err:
        raise HTTPException(status_code=404, detail=err.message) from err


@router.post(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalRequestResponse,
    summary="Approve a pending request",
)
def approve_request(
    approval_id: str,
    decided_by: str = Query(..., description="User identity approving the request"),
    reason: str | None = Query(default=None, description="Approval reason"),
    container: SecurityContainer = Depends(get_container),
) -> ApprovalRequestResponse:
    try:
        decision = ApprovalDecision(
            approval_id=approval_id,
            status=ApprovalStatus.APPROVED,
            decided_by=decided_by,
            reason=reason,
        )
        resolved = container.approval_service.submit_decision(decision)
        return ApprovalRequestResponse.from_domain(resolved)
    except (ApprovalNotFoundError, InvalidApprovalError, PermissionExpiredError) as err:
        raise HTTPException(status_code=err.status_code, detail=err.message) from err


@router.post(
    "/approvals/{approval_id}/deny",
    response_model=ApprovalRequestResponse,
    summary="Deny a pending request",
)
def deny_request(
    approval_id: str,
    decided_by: str = Query(..., description="User identity denying the request"),
    reason: str | None = Query(default=None, description="Denial reason"),
    container: SecurityContainer = Depends(get_container),
) -> ApprovalRequestResponse:
    try:
        decision = ApprovalDecision(
            approval_id=approval_id,
            status=ApprovalStatus.DENIED,
            decided_by=decided_by,
            reason=reason,
        )
        resolved = container.approval_service.submit_decision(decision)
        return ApprovalRequestResponse.from_domain(resolved)
    except (ApprovalNotFoundError, InvalidApprovalError, PermissionExpiredError) as err:
        raise HTTPException(status_code=err.status_code, detail=err.message) from err


@router.post(
    "/approvals/{approval_id}/cancel",
    response_model=ApprovalRequestResponse,
    summary="Cancel a pending request",
)
def cancel_request(
    approval_id: str,
    decided_by: str = Query(..., description="User identity cancelling the request"),
    reason: str | None = Query(default=None, description="Cancel reason"),
    container: SecurityContainer = Depends(get_container),
) -> ApprovalRequestResponse:
    try:
        decision = ApprovalDecision(
            approval_id=approval_id,
            status=ApprovalStatus.CANCELLED,
            decided_by=decided_by,
            reason=reason,
        )
        resolved = container.approval_service.submit_decision(decision)
        return ApprovalRequestResponse.from_domain(resolved)
    except (ApprovalNotFoundError, InvalidApprovalError, PermissionExpiredError) as err:
        raise HTTPException(status_code=err.status_code, detail=err.message) from err


# ---------------------------------------------------------
# Permission Grants Endpoints
# ---------------------------------------------------------


@router.post(
    "/grants",
    response_model=PermissionGrantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a permission grant",
)
def create_grant(
    payload: PermissionGrantRequest,
    container: SecurityContainer = Depends(get_container),
) -> PermissionGrantResponse:
    subject = PermissionSubject(
        subject_type=payload.subject.subject_type,
        subject_id=payload.subject.subject_id,
        name=payload.subject.name,
    )
    resource = PermissionResource(
        resource_type=payload.resource.resource_type,
        resource_id=payload.resource.resource_id,
        location=payload.resource.location,
        owner_id=payload.resource.owner_id,
        sensitivity=payload.resource.sensitivity,
    )
    grant = container.grant_service.create_grant(
        subject=subject,
        action=payload.action,
        resource=resource,
        owner_id=payload.owner_id,
        grant_type=payload.grant_type,
        scope=payload.scope,
        duration_seconds=payload.duration_seconds,
    )
    return PermissionGrantResponse.from_domain(grant)


@router.get(
    "/grants",
    response_model=PaginatedSecurityResponse,
    summary="List permission grants",
)
def list_grants(
    owner_id: str | None = Query(default=None),
    subject_id: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    container: SecurityContainer = Depends(get_container),
) -> PaginatedSecurityResponse:
    grants, total = container.grant_service.list_grants(
        owner_id=owner_id,
        subject_id=subject_id,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    items = [PermissionGrantResponse.from_domain(g) for g in grants]
    return PaginatedSecurityResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/grants/{grant_id}/revoke",
    response_model=PermissionGrantResponse,
    summary="Revoke a permission grant",
)
def revoke_grant(
    grant_id: str,
    container: SecurityContainer = Depends(get_container),
) -> PermissionGrantResponse:
    try:
        revoked = container.grant_service.revoke_grant(grant_id)
        return PermissionGrantResponse.from_domain(revoked)
    except (NotFoundError, PermissionExpiredError) as err:
        raise HTTPException(status_code=err.status_code, detail=err.message) from err


# ---------------------------------------------------------
# Security Mode & Emergency Endpoints
# ---------------------------------------------------------


@router.get(
    "/mode",
    response_model=SecurityModeResponse,
    summary="Get operational security mode state",
)
def get_security_mode(
    container: SecurityContainer = Depends(get_container),
) -> SecurityModeResponse:
    return SecurityModeResponse.from_domain(container.security_mode_service.get_mode())


@router.post(
    "/mode",
    response_model=SecurityModeResponse,
    summary="Set operational security mode state",
)
def set_security_mode(
    payload: SecurityModeRequest,
    container: SecurityContainer = Depends(get_container),
) -> SecurityModeResponse:
    state = container.security_mode_service.set_mode(
        mode=payload.mode,
        changed_by=payload.changed_by,
        reason=payload.reason,
    )
    return SecurityModeResponse.from_domain(state)


@router.get(
    "/emergency",
    response_model=EmergencyBlockResponse,
    summary="Get emergency kill-switch status",
)
def get_emergency_status(
    container: SecurityContainer = Depends(get_container),
) -> EmergencyBlockResponse:
    return EmergencyBlockResponse.from_domain(container.kill_switch_service.get_status())


@router.post(
    "/emergency/activate",
    response_model=EmergencyBlockResponse,
    summary="Activate emergency kill-switch block",
)
def activate_emergency_block(
    payload: EmergencyBlockRequest,
    container: SecurityContainer = Depends(get_container),
) -> EmergencyBlockResponse:
    state = container.kill_switch_service.activate(
        activated_by=payload.activated_by,
        reason=payload.reason,
    )
    return EmergencyBlockResponse.from_domain(state)


@router.post(
    "/emergency/deactivate",
    response_model=EmergencyBlockResponse,
    summary="Deactivate emergency kill-switch block",
)
def deactivate_emergency_block(
    payload: EmergencyBlockRequest,
    container: SecurityContainer = Depends(get_container),
) -> EmergencyBlockResponse:
    state = container.kill_switch_service.deactivate(
        deactivated_by=payload.activated_by,
        reason=payload.reason,
    )
    return EmergencyBlockResponse.from_domain(state)


# ---------------------------------------------------------
# Audit Events & Violations Endpoints
# ---------------------------------------------------------


@router.get(
    "/events",
    response_model=PaginatedSecurityResponse,
    summary="List security audit events",
)
def list_events(
    owner_id: str | None = Query(default=None),
    event_type: SecurityEventType | None = Query(default=None),
    request_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    container: SecurityContainer = Depends(get_container),
) -> PaginatedSecurityResponse:
    events, total = container.audit_service.list_events(
        owner_id=owner_id,
        event_type=event_type,
        request_id=request_id,
        limit=limit,
        offset=offset,
    )
    items = [SecurityEventResponse.from_domain(e) for e in events]
    return PaginatedSecurityResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/violations",
    response_model=PaginatedSecurityResponse,
    summary="List security violations",
)
def list_violations(
    owner_id: str | None = Query(default=None),
    violation_type: SecurityViolationType | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    container: SecurityContainer = Depends(get_container),
) -> PaginatedSecurityResponse:
    violations, total = container.violation_service.list_violations(
        owner_id=owner_id,
        violation_type=violation_type,
        limit=limit,
        offset=offset,
    )
    items = [SecurityViolationResponse.from_domain(v) for v in violations]
    return PaginatedSecurityResponse(items=items, total=total, limit=limit, offset=offset)
