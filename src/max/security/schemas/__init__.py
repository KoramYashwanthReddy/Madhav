"""Pydantic API schemas for Module 15 — Permission & Security."""

from max.security.schemas.requests import (
    ApprovalDecisionRequest,
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

__all__ = [
    "PermissionCheckRequest",
    "PolicyCreateRequest",
    "PolicyUpdateRequest",
    "ApprovalDecisionRequest",
    "PermissionGrantRequest",
    "SecurityModeRequest",
    "EmergencyBlockRequest",
    "PermissionDecisionResponse",
    "PolicyResponse",
    "ApprovalRequestResponse",
    "PermissionGrantResponse",
    "SecurityModeResponse",
    "EmergencyBlockResponse",
    "SecurityEventResponse",
    "SecurityViolationResponse",
    "PaginatedSecurityResponse",
]
