"""ApprovalService for human approval request lifecycle management."""

from datetime import UTC, datetime, timedelta

from max.security.domain.approval import ApprovalDecision, ApprovalRequest
from max.security.domain.enums import (
    ApprovalStatus,
    ApprovalType,
    PermissionAction,
    PermissionGrantType,
    RiskLevel,
    SecurityEventType,
)
from max.security.domain.exceptions import (
    ApprovalNotFoundError,
    InvalidApprovalError,
    PermissionExpiredError,
)
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject
from max.security.repositories.approval_repository import BaseApprovalRepository
from max.security.repositories.permission_repository import BasePermissionGrantRepository
from max.security.services.audit_service import SecurityAuditService


class ApprovalService:
    """Service for managing human approval requests, user decisions, and grant generation."""

    def __init__(
        self,
        approval_repository: BaseApprovalRepository,
        grant_repository: BasePermissionGrantRepository | None = None,
        audit_service: SecurityAuditService | None = None,
        default_timeout_seconds: float = 3600.0,
    ) -> None:
        self._approval_repo = approval_repository
        self._grant_repo = grant_repository
        self._audit_service = audit_service
        self._default_timeout = default_timeout_seconds

    def create_approval_request(
        self,
        permission_request_id: str,
        title: str,
        explanation: str,
        risk_level: RiskLevel,
        requested_action: PermissionAction,
        requested_resource: PermissionResource,
        owner_id: str,
        subject: PermissionSubject | None = None,
        approval_type: ApprovalType = ApprovalType.USER_CONFIRMATION,
        timeout_seconds: float | None = None,
    ) -> ApprovalRequest:
        """Create a new human approval request for a pending action."""
        now = datetime.now(UTC)
        duration = (
            timeout_seconds if timeout_seconds and timeout_seconds > 0 else self._default_timeout
        )
        expires_at = now + timedelta(seconds=duration)

        from max.security.domain.enums import PermissionSubjectType
        from max.security.domain.subject import PermissionSubject

        req_subject = subject or PermissionSubject(
            subject_type=PermissionSubjectType.USER, subject_id=owner_id
        )

        approval = ApprovalRequest(
            permission_request_id=permission_request_id,
            subject=req_subject,
            title=title,
            explanation=explanation,
            risk_level=risk_level,
            requested_action=requested_action,
            requested_resource=requested_resource,
            owner_id=owner_id,
            status=ApprovalStatus.PENDING,
            approval_type=approval_type,
            expires_at=expires_at,
            created_at=now,
        )

        saved = self._approval_repo.save(approval)

        if self._audit_service:
            self._audit_service.record_event(
                event_type=SecurityEventType.APPROVAL_REQUESTED,
                owner_id=owner_id,
                request_id=permission_request_id,
                summary=f"Human approval requested for '{requested_action.value}' on '{requested_resource.resource_id}' (Approval ID: {saved.approval_id})",
                metadata={"approval_id": saved.approval_id, "risk_level": risk_level.value},
            )

        return saved

    def get_approval(self, approval_id: str) -> ApprovalRequest:
        """Get approval request by ID."""
        approval = self._approval_repo.get_by_id(approval_id)
        if not approval:
            raise ApprovalNotFoundError(f"Approval request '{approval_id}' not found.")
        return approval

    def get_by_permission_request_id(self, permission_request_id: str) -> ApprovalRequest | None:
        """Get approval by associated permission request ID."""
        return self._approval_repo.get_by_permission_request_id(permission_request_id)

    def list_approvals(
        self,
        owner_id: str | None = None,
        status: ApprovalStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ApprovalRequest], int]:
        """List approval requests with filtering."""
        return self._approval_repo.list_approvals(
            owner_id=owner_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    def submit_decision(self, decision: ApprovalDecision) -> ApprovalRequest:
        """Process user approval decision (APPROVED, DENIED, CANCELLED)."""
        approval = self.get_approval(decision.approval_id)

        if approval.status != ApprovalStatus.PENDING:
            raise InvalidApprovalError(
                f"Approval request '{decision.approval_id}' is already finalized with status '{approval.status.value}'."
            )

        now = datetime.now(UTC)
        if now > approval.expires_at:
            expired_approval = approval.model_copy(
                update={"status": ApprovalStatus.EXPIRED, "decided_at": now}
            )
            self._approval_repo.save(expired_approval)
            raise PermissionExpiredError(f"Approval request '{decision.approval_id}' has expired.")

        if decision.status not in {
            ApprovalStatus.APPROVED,
            ApprovalStatus.DENIED,
            ApprovalStatus.CANCELLED,
        }:
            raise InvalidApprovalError(
                f"Invalid decision status: '{decision.status}'. Must be APPROVED, DENIED, or CANCELLED."
            )

        updated = approval.model_copy(
            update={
                "status": decision.status,
                "decided_at": now,
                "decided_by": decision.decided_by,
                "decision_reason": decision.reason,
            }
        )
        saved = self._approval_repo.save(updated)

        # If APPROVED, create a ONE_TIME permission grant for the requesting subject!
        if decision.status == ApprovalStatus.APPROVED and self._grant_repo:
            from max.security.domain.enums import PermissionScope
            from max.security.domain.grant import PermissionGrant

            grant = PermissionGrant(
                subject=approval.subject,
                action=approval.requested_action,
                resource=approval.requested_resource,
                scope=PermissionScope.EXACT_RESOURCE,
                grant_type=PermissionGrantType.ONE_TIME,
                owner_id=approval.owner_id,
                created_at=now,
                expires_at=now + timedelta(seconds=1800),  # 30 min window for approved execution
            )
            self._grant_repo.save(grant)

        if self._audit_service:
            event_type = (
                SecurityEventType.APPROVAL_APPROVED
                if decision.status == ApprovalStatus.APPROVED
                else SecurityEventType.APPROVAL_DENIED
            )
            self._audit_service.record_event(
                event_type=event_type,
                owner_id=approval.owner_id,
                request_id=approval.permission_request_id,
                summary=f"Approval decision '{decision.status.value}' for request '{approval.approval_id}' by user '{decision.decided_by}'",
                metadata={"approval_id": approval.approval_id, "status": decision.status.value},
            )

        return saved
