"""Human-in-the-Loop Approval Management Service."""

import datetime
import logging

from max.autonomy.domain import ApprovalRequest, ApprovalStatus, Mission, RiskLevel
from max.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ApprovalService:
    """Manages human approval requests, expiration timers, and audit state."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._approvals: dict[str, ApprovalRequest] = {}

    def create_approval_request(
        self,
        mission: Mission,
        action_name: str,
        risk_level: RiskLevel,
        reason: str,
        impact_summary: str,
        timeout_seconds: int = 600,
    ) -> ApprovalRequest:
        """Create new pending approval request with expiration timestamp."""
        now = datetime.datetime.now(datetime.UTC)
        expires_at = (now + datetime.timedelta(seconds=timeout_seconds)).isoformat()
        approval_id = f"appr_{mission.mission_id}_{len(self._approvals) + 1}"

        req = ApprovalRequest(
            approval_id=approval_id,
            mission_id=mission.mission_id,
            action_name=action_name,
            risk_level=risk_level,
            reason=reason,
            impact_summary=impact_summary,
            requested_at=now.isoformat(),
            expires_at=expires_at,
            status=ApprovalStatus.PENDING,
        )
        self._approvals[approval_id] = req
        mission.approvals.append(req)
        logger.info(
            "Created approval request %s for action '%s' in mission %s (Risk: %s, Expires in %ds).",
            approval_id,
            action_name,
            mission.mission_id,
            risk_level.value,
            timeout_seconds,
        )
        return req

    def get_approval(self, approval_id: str) -> ApprovalRequest:
        """Retrieve approval request by ID with automatic expiration check."""
        if approval_id not in self._approvals:
            raise ValueError(f"Approval request '{approval_id}' not found.")

        req = self._approvals[approval_id]
        self._check_expiration(req)
        return req

    def list_pending_approvals(self, mission_id: str | None = None) -> list[ApprovalRequest]:
        """List active pending approval requests."""
        pending = []
        for req in self._approvals.values():
            self._check_expiration(req)
            if req.status == ApprovalStatus.PENDING:
                if mission_id is None or req.mission_id == mission_id:
                    pending.append(req)
        return pending

    def approve_request(self, approval_id: str, user_id: str = "user_admin") -> ApprovalRequest:
        """Approve a pending approval request."""
        req = self.get_approval(approval_id)
        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot approve request '{approval_id}' in status '{req.status.value}'.")

        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        req.status = ApprovalStatus.APPROVED
        req.approved_by = user_id
        req.decision_at = now_iso
        logger.info("Approval request %s APPROVED by user '%s'.", approval_id, user_id)
        return req

    def deny_request(self, approval_id: str, user_id: str = "user_admin") -> ApprovalRequest:
        """Deny a pending approval request."""
        req = self.get_approval(approval_id)
        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot deny request '{approval_id}' in status '{req.status.value}'.")

        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        req.status = ApprovalStatus.DENIED
        req.approved_by = user_id
        req.decision_at = now_iso
        logger.info("Approval request %s DENIED by user '%s'.", approval_id, user_id)
        return req

    def _check_expiration(self, req: ApprovalRequest) -> None:
        """Check if request has passed expiration timestamp and mark EXPIRED."""
        if req.status == ApprovalStatus.PENDING:
            now_iso = datetime.datetime.now(datetime.UTC).isoformat()
            if now_iso > req.expires_at:
                req.status = ApprovalStatus.EXPIRED
                logger.warning("Approval request %s EXPIRED.", req.approval_id)
