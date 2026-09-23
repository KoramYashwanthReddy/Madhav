"""SecurityContextBuilder for assembling unified evaluation context."""

from datetime import UTC, datetime

from max.security.domain.decision import PermissionRequest, SecurityContext
from max.security.domain.enums import SecurityMode
from max.security.domain.subject import SecurityPrincipal
from max.security.utils.domain_url import normalize_domain_or_url
from max.security.utils.path import normalize_path


class SecurityContextBuilder:
    """Builder for constructing normalized SecurityContext objects from requests."""

    def build_context(
        self,
        request: PermissionRequest,
        security_mode: SecurityMode = SecurityMode.NORMAL,
        emergency_block_active: bool = False,
        policy_version: int = 1,
    ) -> SecurityContext:
        """Construct normalized SecurityContext from PermissionRequest."""

        # Normalize resource location if file path or URL
        normalized_resource = request.resource.model_copy()
        if normalized_resource.location:
            if normalized_resource.resource_type.upper() in {"FILE", "DIRECTORY"}:
                normalized_resource.location = normalize_path(normalized_resource.location)
            elif normalized_resource.resource_type.upper() in {"BROWSER", "WEBSITE", "URL"}:
                norm_domain = normalize_domain_or_url(normalized_resource.location)
                normalized_resource.location = (
                    norm_domain["hostname"] or normalized_resource.location
                )

        # Build security principal
        principal = SecurityPrincipal(
            subject=request.subject,
            owner_id=request.owner_id,
            roles=["user"] if request.subject.subject_type == "USER" else ["agent"],
        )

        return SecurityContext(
            principal=principal,
            owner_id=request.owner_id,
            agent_id=request.agent_id,
            agent_run_id=request.agent_run_id,
            tool_id=request.tool_reference,
            action=request.action,
            resource=normalized_resource,
            task_id=request.task_id,
            plan_id=request.plan_id,
            conversation_id=request.conversation_id,
            risk_level=request.risk_level,
            security_mode=security_mode,
            emergency_block_active=emergency_block_active,
            policy_version=policy_version,
            arguments=request.arguments,
            timestamp=datetime.now(UTC),
        )
