"""Global dependency injection container for Module 19 — Application Control."""

from max.config.settings import get_settings
from max.application_control.backends.base import ApplicationControlBackend
from max.application_control.backends.mock import MockApplicationControlBackend
from max.application_control.backends.windows import WindowsApplicationControlBackend
from max.application_control.repositories.repositories import (
    ApplicationAuditRepository,
    ApplicationInstanceRepository,
    ApplicationPolicyRepository,
    ApplicationRepository,
)
from max.application_control.security.app_policy import ApplicationPolicyService
from max.application_control.services.application_control_service import ApplicationControlService
from max.security.container import get_security_container
from max.security.services.gate import PermissionGate


class ApplicationControlContainer:
    """Dependency injection container for the Application Control subsystem."""

    def __init__(
        self,
        use_mock_backend: bool | None = None,
        custom_backend: ApplicationControlBackend | None = None,
    ) -> None:
        cfg = get_settings().application_control
        self.settings = cfg

        # Repositories
        self.app_repo = ApplicationRepository()
        self.instance_repo = ApplicationInstanceRepository()
        self.policy_repo = ApplicationPolicyRepository()
        self.audit_repo = ApplicationAuditRepository()

        # Module 15 Permission Gate integration
        self.permission_gate: PermissionGate | None = None
        try:
            sec_container = get_security_container()
            self.permission_gate = sec_container.gate
        except Exception:
            self.permission_gate = None

        # Safety policy service
        self.policy_service = ApplicationPolicyService(
            settings=cfg,
            policy_repo=self.policy_repo,
            instance_repo=self.instance_repo,
            permission_gate=self.permission_gate,
        )

        # Backend selection
        if custom_backend is not None:
            self.backend: ApplicationControlBackend = custom_backend
        elif use_mock_backend or (use_mock_backend is None and cfg.dry_run):
            self.backend = MockApplicationControlBackend()
        else:
            self.backend = WindowsApplicationControlBackend()

        # Primary service facade
        self.application_control_service = ApplicationControlService(
            backend=self.backend,
            settings=cfg,
            app_repo=self.app_repo,
            instance_repo=self.instance_repo,
            policy_repo=self.policy_repo,
            audit_repo=self.audit_repo,
            policy_service=self.policy_service,
        )


_container_instance: ApplicationControlContainer | None = None


def get_application_control_container(
    use_mock_backend: bool | None = None,
) -> ApplicationControlContainer:
    """Retrieve or initialize the global ApplicationControlContainer instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = ApplicationControlContainer(
            use_mock_backend=use_mock_backend
        )
    return _container_instance


def reset_application_control_container() -> None:
    """Reset the global ApplicationControlContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None
