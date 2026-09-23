"""Domain models for Module 15 — Permission & Security."""

from max.security.domain.action import ActionDefinition
from max.security.domain.approval import ApprovalDecision, ApprovalRequest
from max.security.domain.audit import SecurityEvent, SecurityViolation
from max.security.domain.boundary import AuthorizedExecutionRequest
from max.security.domain.decision import PermissionDecision, PermissionRequest, SecurityContext
from max.security.domain.emergency import EmergencyBlock, SecurityModeState
from max.security.domain.enums import (
    ApprovalStatus,
    ApprovalType,
    DecisionReason,
    PermissionAction,
    PermissionDecisionStatus,
    PermissionEffect,
    PermissionGrantType,
    PermissionScope,
    PermissionSubjectType,
    RequestStatus,
    ResourceSensitivity,
    RiskLevel,
    SecurityEventType,
    SecurityMode,
    SecurityViolationType,
)
from max.security.domain.exceptions import (
    ApprovalNotFoundError,
    EmergencyBlockError,
    InvalidApprovalError,
    InvalidPolicyError,
    PermissionDeniedError,
    PermissionExpiredError,
    PermissionRequiredError,
    SecurityContextError,
    SecurityError,
    SecurityEvaluationError,
    SecurityModeError,
    SecurityViolationError,
)
from max.security.domain.grant import PermissionGrant
from max.security.domain.permission import (
    Permission,
    PermissionCondition,
    PermissionPolicy,
    PermissionRule,
)
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject, SecurityPrincipal

__all__ = [
    # Enums
    "PermissionSubjectType",
    "PermissionAction",
    "ResourceSensitivity",
    "PermissionScope",
    "PermissionEffect",
    "RiskLevel",
    "PermissionDecisionStatus",
    "DecisionReason",
    "RequestStatus",
    "ApprovalStatus",
    "ApprovalType",
    "PermissionGrantType",
    "SecurityMode",
    "SecurityEventType",
    "SecurityViolationType",
    # Domain models
    "PermissionSubject",
    "SecurityPrincipal",
    "PermissionResource",
    "ActionDefinition",
    "PermissionCondition",
    "PermissionRule",
    "PermissionPolicy",
    "Permission",
    "SecurityContext",
    "PermissionRequest",
    "PermissionDecision",
    "ApprovalRequest",
    "ApprovalDecision",
    "PermissionGrant",
    "EmergencyBlock",
    "SecurityModeState",
    "SecurityEvent",
    "SecurityViolation",
    "AuthorizedExecutionRequest",
    # Exceptions
    "SecurityError",
    "PermissionDeniedError",
    "PermissionRequiredError",
    "PermissionExpiredError",
    "EmergencyBlockError",
    "SecurityModeError",
    "SecurityViolationError",
    "SecurityContextError",
    "SecurityEvaluationError",
    "InvalidPolicyError",
    "ApprovalNotFoundError",
    "InvalidApprovalError",
]
