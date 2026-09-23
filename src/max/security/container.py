"""Global container and dependency resolution for Module 15 — Permission & Security."""

from max.config.settings import get_settings
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
from max.security.services.approval_service import ApprovalService
from max.security.services.audit_service import SecurityAuditService, SecurityViolationService
from max.security.services.context_builder import SecurityContextBuilder
from max.security.services.evaluator import PermissionEvaluator
from max.security.services.gate import PermissionGate
from max.security.services.grant_service import PermissionGrantService
from max.security.services.kill_switch_service import KillSwitchService
from max.security.services.policy_service import PolicyService
from max.security.services.security_mode_service import SecurityModeService


class SecurityContainer:
    """Singleton container managing repositories and services for security subsystem."""

    def __init__(self) -> None:
        cfg = get_settings().security_module

        # Repositories
        self.policy_repo: BasePolicyRepository = InMemoryPolicyRepository()
        self.grant_repo: BasePermissionGrantRepository = InMemoryPermissionGrantRepository()
        self.request_repo: BasePermissionRequestRepository = InMemoryPermissionRequestRepository()
        self.decision_repo: BasePermissionDecisionRepository = (
            InMemoryPermissionDecisionRepository()
        )
        self.approval_repo: BaseApprovalRepository = InMemoryApprovalRepository()
        self.event_repo: BaseSecurityEventRepository = InMemorySecurityEventRepository()
        self.violation_repo: BaseSecurityViolationRepository = InMemorySecurityViolationRepository()

        # Services
        self.audit_service = SecurityAuditService(event_repository=self.event_repo)
        self.violation_service = SecurityViolationService(
            violation_repository=self.violation_repo,
            audit_service=self.audit_service,
        )
        self.security_mode_service = SecurityModeService(
            default_mode=cfg.default_mode,  # type: ignore[arg-type]
            audit_service=self.audit_service,
        )
        self.kill_switch_service = KillSwitchService(
            default_block=cfg.emergency_block,
            audit_service=self.audit_service,
        )
        self.policy_service = PolicyService(
            policy_repository=self.policy_repo,
            audit_service=self.audit_service,
        )
        self.grant_service = PermissionGrantService(
            grant_repository=self.grant_repo,
            audit_service=self.audit_service,
        )
        self.approval_service = ApprovalService(
            approval_repository=self.approval_repo,
            grant_repository=self.grant_repo,
            audit_service=self.audit_service,
            default_timeout_seconds=cfg.approval_timeout,
        )
        self.context_builder = SecurityContextBuilder()
        self.evaluator = PermissionEvaluator(
            policy_repository=self.policy_repo,
            grant_repository=self.grant_repo,
        )
        self.gate = PermissionGate(
            evaluator=self.evaluator,
            request_repository=self.request_repo,
            decision_repository=self.decision_repo,
            context_builder=self.context_builder,
            security_mode_service=self.security_mode_service,
            kill_switch_service=self.kill_switch_service,
            approval_service=self.approval_service,
            audit_service=self.audit_service,
            violation_service=self.violation_service,
        )


_container_instance: SecurityContainer | None = None


def get_security_container() -> SecurityContainer:
    """Retrieve global SecurityContainer singleton."""
    global _container_instance
    if _container_instance is None:
        _container_instance = SecurityContainer()
    return _container_instance


def reset_security_container() -> None:
    """Reset global SecurityContainer instance (for test isolation)."""
    global _container_instance
    _container_instance = None
