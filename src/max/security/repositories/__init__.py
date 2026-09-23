"""Repositories for Module 15 — Permission & Security."""

from max.security.repositories.approval_repository import (
    BaseApprovalRepository,
    InMemoryApprovalRepository,
)
from max.security.repositories.audit_repository import (
    BaseSecurityEventRepository,
    BaseSecurityViolationRepository,
    InMemorySecurityEventRepository,
    InMemorySecurityViolationRepository,
)
from max.security.repositories.permission_repository import (
    BasePermissionGrantRepository,
    InMemoryPermissionGrantRepository,
)
from max.security.repositories.policy_repository import (
    BasePolicyRepository,
    InMemoryPolicyRepository,
)
from max.security.repositories.request_repository import (
    BasePermissionDecisionRepository,
    BasePermissionRequestRepository,
    InMemoryPermissionDecisionRepository,
    InMemoryPermissionRequestRepository,
)

__all__ = [
    "BasePolicyRepository",
    "InMemoryPolicyRepository",
    "BasePermissionGrantRepository",
    "InMemoryPermissionGrantRepository",
    "BasePermissionRequestRepository",
    "InMemoryPermissionRequestRepository",
    "BasePermissionDecisionRepository",
    "InMemoryPermissionDecisionRepository",
    "BaseApprovalRepository",
    "InMemoryApprovalRepository",
    "BaseSecurityEventRepository",
    "InMemorySecurityEventRepository",
    "BaseSecurityViolationRepository",
    "InMemorySecurityViolationRepository",
]
