"""PermissionGate — Central security entry point for permission checks."""

from datetime import UTC, datetime, timedelta

from max.security.domain.boundary import AuthorizedExecutionRequest
from max.security.domain.decision import PermissionDecision, PermissionRequest
from max.security.domain.enums import (
    PermissionDecisionStatus,
    SecurityEventType,
    SecurityViolationType,
)
from max.security.repositories.request_repository import (
    BasePermissionDecisionRepository,
    BasePermissionRequestRepository,
)
from max.security.services.approval_service import ApprovalService
from max.security.services.audit_service import SecurityAuditService, SecurityViolationService
from max.security.services.context_builder import SecurityContextBuilder
from max.security.services.evaluator import PermissionEvaluator
from max.security.services.kill_switch_service import KillSwitchService
from max.security.services.security_mode_service import SecurityModeService


class PermissionGate:
    """Primary security gate enforcing permission checks before execution."""

    def __init__(
        self,
        evaluator: PermissionEvaluator,
        request_repository: BasePermissionRequestRepository,
        decision_repository: BasePermissionDecisionRepository,
        context_builder: SecurityContextBuilder | None = None,
        security_mode_service: SecurityModeService | None = None,
        kill_switch_service: KillSwitchService | None = None,
        approval_service: ApprovalService | None = None,
        audit_service: SecurityAuditService | None = None,
        violation_service: SecurityViolationService | None = None,
    ) -> None:
        self._evaluator = evaluator
        self._request_repo = request_repository
        self._decision_repo = decision_repository
        self._context_builder = context_builder or SecurityContextBuilder()
        self._mode_service = security_mode_service
        self._kill_switch_service = kill_switch_service
        self._approval_service = approval_service
        self._audit_service = audit_service
        self._violation_service = violation_service

    def check(self, request: PermissionRequest) -> PermissionDecision:
        """Evaluate permission request and return structured decision."""
        # 1. Save permission request record
        self._request_repo.save(request)

        # 2. Get current security mode and emergency block status
        sec_mode = self._mode_service.get_mode().mode if self._mode_service else "NORMAL"
        emergency_active = (
            self._kill_switch_service.is_active() if self._kill_switch_service else False
        )

        # 3. Build security context
        context = self._context_builder.build_context(
            request=request,
            security_mode=sec_mode,  # type: ignore[arg-type]
            emergency_block_active=emergency_active,
        )

        # 4. Audit permission requested
        if self._audit_service:
            self._audit_service.record_event(
                event_type=SecurityEventType.PERMISSION_REQUESTED,
                owner_id=request.owner_id,
                request_id=request.request_id,
                tool_id=request.tool_reference,
                action=request.action,
                resource_id=request.resource.resource_id,
                summary=f"Permission check requested: '{request.action.value}' on '{request.resource.resource_id}'",
            )

        # 5. Evaluate decision
        decision = self._evaluator.evaluate(context=context, request_id=request.request_id)

        # 6. Handle approval creation if required
        if decision.status == PermissionDecisionStatus.REQUIRES_APPROVAL and self._approval_service:
            approval_req = self._approval_service.create_approval_request(
                permission_request_id=request.request_id,
                title=f"Approval needed for '{request.action.value}' on {request.resource.resource_id}",
                explanation=f"Action '{request.action.value}' on resource '{request.resource.resource_id}' requires explicit human approval.",
                risk_level=request.risk_level,
                requested_action=request.action,
                requested_resource=request.resource,
                owner_id=request.owner_id,
                subject=request.subject,
            )
            decision = decision.model_copy(update={"approval_request_id": approval_req.approval_id})

        # 7. Record decision
        self._decision_repo.save(decision)

        # 8. Record audit log & violations if denied/blocked
        if self._audit_service:
            event_type = (
                SecurityEventType.PERMISSION_ALLOWED
                if decision.status == PermissionDecisionStatus.ALLOWED
                else SecurityEventType.PERMISSION_DENIED
            )
            self._audit_service.record_event(
                event_type=event_type,
                owner_id=request.owner_id,
                request_id=request.request_id,
                decision_id=decision.decision_id,
                tool_id=request.tool_reference,
                action=request.action,
                resource_id=request.resource.resource_id,
                summary=f"Permission decision '{decision.status.value}' for request '{request.request_id}': {decision.message}",
            )

        if (
            decision.status in {PermissionDecisionStatus.BLOCKED, PermissionDecisionStatus.ERROR}
            and self._violation_service
        ):
            v_type = (
                SecurityViolationType.BLOCKED_ACTION_ATTEMPT
                if decision.status == PermissionDecisionStatus.BLOCKED
                else SecurityViolationType.EVALUATION_FAILURE
            )
            self._violation_service.record_violation(
                violation_type=v_type,
                owner_id=request.owner_id,
                summary=f"Action '{request.action.value}' was blocked: {decision.message}",
                tool_id=request.tool_reference,
                details={"request_id": request.request_id, "decision_id": decision.decision_id},
            )

        return decision

    def check_and_authorize(
        self, request: PermissionRequest, validity_seconds: float = 300.0
    ) -> tuple[PermissionDecision, AuthorizedExecutionRequest | None]:
        """Check request and return decision alongside AuthorizedExecutionRequest if allowed."""
        decision = self.check(request)

        if decision.status == PermissionDecisionStatus.ALLOWED:
            now = datetime.now(UTC)
            expiry = now + timedelta(seconds=validity_seconds)
            auth_token = AuthorizedExecutionRequest(
                permission_decision_id=decision.decision_id,
                tool_reference=request.tool_reference,
                action=request.action,
                resource=request.resource,
                subject=request.subject,
                owner_id=request.owner_id,
                authorization_expiry=expiry,
                arguments=request.arguments,
            )
            return decision, auth_token

        return decision, None
