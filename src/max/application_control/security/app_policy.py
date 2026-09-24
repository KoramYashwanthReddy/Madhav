"""Application Policy & Security Enforcement Service for Module 19.

Evaluates safety policies, permission gates, path security, elevation checks,
and instance limits before executing any application control actions.
"""

from typing import Any
import os
import uuid

from max.config.sections import ApplicationControlSettings
from max.application_control.domain.enums import ApplicationType
from max.application_control.domain.exceptions import (
    ApplicationBlockedError,
    ApplicationElevationDeniedError,
    ApplicationInstanceLimitExceededError,
    ApplicationPolicyViolationError,
)
from max.application_control.domain.models import Application, ApplicationPolicy
from max.application_control.repositories.repositories import (
    ApplicationInstanceRepository,
    ApplicationPolicyRepository,
)
from max.security.services.gate import PermissionGate


class ApplicationPolicyService:
    """Evaluates safety policies and permissions for Application Control operations."""

    def __init__(
        self,
        settings: ApplicationControlSettings | None = None,
        policy_repo: ApplicationPolicyRepository | None = None,
        instance_repo: ApplicationInstanceRepository | None = None,
        permission_gate: PermissionGate | None = None,
    ) -> None:
        self.settings = settings or ApplicationControlSettings()
        self.policy_repo = policy_repo or ApplicationPolicyRepository()
        self.instance_repo = instance_repo or ApplicationInstanceRepository()
        self.permission_gate = permission_gate

    def validate_launch(
        self,
        app: Application,
        elevate: bool = False,
        args: list[str] | None = None,
    ) -> None:
        """Validate if an application can be launched under current policies and permissions."""
        if not self.settings.enabled:
            raise ApplicationPolicyViolationError(
                f"Application control subsystem is disabled."
            )

        exe_path = app.executable.path if (app.executable and hasattr(app.executable, "path")) else str(app.executable or "")
        exe_name = os.path.basename(exe_path).lower()

        # Check global blocked executables
        blocked = [b.lower() for b in self.settings.blocked_executables]
        if exe_name in blocked or exe_path.lower() in blocked:
            raise ApplicationBlockedError(
                f"Executable '{exe_path}' is in the global blocklist."
            )

        # Check global allowed executables if specified
        if self.settings.allowed_executables:
            allowed = [a.lower() for a in self.settings.allowed_executables]
            if exe_name not in allowed and exe_path.lower() not in allowed:
                raise ApplicationBlockedError(
                    f"Executable '{exe_path}' is not in the allowed executables list."
                )

        # Check system app policy
        if app.app_type == ApplicationType.SYSTEM and not self.settings.allow_system_apps:
            raise ApplicationBlockedError(
                f"Launching system application '{app.display_name}' is disabled by settings."
            )

        # Check per-app policy
        policy = self.policy_repo.get(app.app_id)
        if policy:
            if not policy.allowed:
                raise ApplicationBlockedError(
                    f"Application '{app.display_name}' is disabled by per-application policy."
                )
            if elevate and not policy.allow_elevation:
                raise ApplicationElevationDeniedError(
                    f"Elevation is denied for application '{app.display_name}' by policy."
                )

        # Check max instances
        active_count = self.instance_repo.count_active_for_app(app.app_id)
        max_instances = (
            policy.max_instances if (policy and policy.max_instances is not None)
            else self.settings.max_instances_per_app
        )
        if active_count >= max_instances:
            raise ApplicationInstanceLimitExceededError(
                f"Cannot launch '{app.display_name}': active instances ({active_count}) reach limit of {max_instances}."
            )

        # Check Module 15 Permission Gate if attached
        if self.permission_gate is not None:
            from max.security.domain.enums import PermissionAction, PermissionSubjectType, ResourceSensitivity, RiskLevel
            from max.security.domain.permission import PermissionRequest
            from max.security.domain.resource import PermissionResource
            from max.security.domain.subject import PermissionSubject

            perm_req = PermissionRequest(
                request_id=f"app_perm_{uuid.uuid4().hex[:12]}",
                owner_id="system",
                subject=PermissionSubject(
                    subject_id="agent_application_control",
                    subject_type=PermissionSubjectType.AGENT,
                ),
                resource=PermissionResource(
                    resource_type="APPLICATION",
                    resource_id=f"app.launch.{app.app_id}",
                    owner_id="system",
                    sensitivity=ResourceSensitivity.NORMAL,
                    attributes={
                        "app_name": app.display_name,
                        "executable": app.executable,
                        "elevate": elevate,
                    },
                ),
                action=PermissionAction.EXECUTE,
                risk_level=RiskLevel.HIGH if elevate else RiskLevel.MEDIUM,
                tool_reference="app.launch",
            )
            decision = self.permission_gate.check_permission(perm_req)
            if not decision.is_allowed:
                raise ApplicationPolicyViolationError(
                    f"Permission denied to launch '{app.display_name}': {decision.reason}"
                )

    def validate_action(
        self,
        app: Application,
        action_name: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Validate non-launch action (close, focus, restart, etc.)."""
        if not self.settings.enabled:
            raise ApplicationPolicyViolationError(
                "Application control subsystem is disabled."
            )

        policy = self.policy_repo.get(app.app_id)
        if policy and not policy.allowed:
            raise ApplicationBlockedError(
                f"Application '{app.display_name}' is disabled by per-application policy."
            )

        if self.permission_gate is not None:
            from max.security.domain.enums import PermissionAction, PermissionSubjectType, ResourceSensitivity, RiskLevel
            from max.security.domain.permission import PermissionRequest
            from max.security.domain.resource import PermissionResource
            from max.security.domain.subject import PermissionSubject

            perm_req = PermissionRequest(
                request_id=f"app_perm_{uuid.uuid4().hex[:12]}",
                owner_id="system",
                subject=PermissionSubject(
                    subject_id="agent_application_control",
                    subject_type=PermissionSubjectType.AGENT,
                ),
                resource=PermissionResource(
                    resource_type="APPLICATION",
                    resource_id=f"{action_name}.{app.app_id}",
                    owner_id="system",
                    sensitivity=ResourceSensitivity.NORMAL,
                    attributes=context or {},
                ),
                action=PermissionAction.EXECUTE,
                risk_level=RiskLevel.MEDIUM,
                tool_reference=action_name,
            )
            decision = self.permission_gate.check_permission(perm_req)
            if not decision.is_allowed:
                raise ApplicationPolicyViolationError(
                    f"Permission denied for action '{action_name}' on '{app.display_name}': {decision.reason}"
                )

