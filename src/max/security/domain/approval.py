"""Domain models for approval requests and human approval decisions."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import ApprovalStatus, ApprovalType, PermissionAction, RiskLevel
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject


class ApprovalRequest(BaseModel):
    """Pending or finalized human approval request model."""

    approval_id: str = Field(
        default_factory=lambda: f"appr_{uuid.uuid4().hex[:12]}",
        description="Unique approval request identifier",
    )
    permission_request_id: str = Field(..., description="Target permission request identifier")
    subject: PermissionSubject = Field(..., description="Subject requesting permission")
    title: str = Field(..., description="Human-understandable summary title")
    explanation: str = Field(
        ..., description="Clear explanation of the requested action and purpose"
    )
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    requested_action: PermissionAction = Field(..., description="Requested permission action")
    requested_resource: PermissionResource = Field(..., description="Target resource description")
    owner_id: str = Field(..., description="Target resource/system owner ID")
    status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING, description="Approval request status"
    )
    approval_type: ApprovalType = Field(
        default=ApprovalType.USER_CONFIRMATION, description="Classification of approval type"
    )
    expires_at: datetime = Field(..., description="Approval request expiration timestamp")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    decided_at: datetime | None = Field(default=None, description="Resolution timestamp")
    decided_by: str | None = Field(default=None, description="Identity of approving user")
    decision_reason: str | None = Field(default=None, description="User justification or rationale")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata tags")


class ApprovalDecision(BaseModel):
    """Input parameters for submitting an approval decision."""

    approval_id: str = Field(..., description="Target approval request ID")
    status: ApprovalStatus = Field(..., description="Decision status (APPROVED, DENIED, CANCELLED)")
    decided_by: str = Field(..., description="User identity rendering the decision")
    reason: str | None = Field(default=None, description="User-provided decision rationale")
