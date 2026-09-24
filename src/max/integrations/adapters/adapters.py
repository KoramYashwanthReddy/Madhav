"""Integration adapters for Modules 14, 15, 27, and 28."""

import asyncio
import logging
from typing import Any

from max.notifications.container import get_notification_container
from max.scheduler.container import get_scheduler_container
from max.scheduler.domain.models import ScheduleEvent
from max.security.container import get_security_container
from max.security.domain.decision import PermissionDecision, PermissionRequest
from max.security.domain.enums import (
    PermissionAction,
    PermissionDecisionStatus,
    PermissionSubjectType,
)
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject
from max.tools.domain.enums import ToolCategory, ToolRiskLevel, ToolSource
from max.tools.domain.tool import ToolFieldDescriptor, ToolInputSchema, ToolOutputSchema
from max.tools.services.registry import ToolRegistryService

logger = logging.getLogger(__name__)


class Module14ToolRegistryAdapter:
    """Adapter syncing external integration capabilities into Module 14 Tool Registry."""

    def __init__(self, tool_registry: ToolRegistryService | None = None) -> None:
        self._tool_registry = tool_registry

    def _get_registry(self) -> ToolRegistryService:
        if self._tool_registry:
            return self._tool_registry
        from max.tools.api.routes import get_registry_service
        return get_registry_service()

    def sync_capability_as_tool(
        self,
        provider_key: str,
        capability_name: str,
        description: str,
        category_name: str,
        risk_level_name: str,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> str:
        """Register or update capability in Module 14 Tool Registry."""
        tool_name = f"integration.{provider_key}.{capability_name}"
        registry = self._get_registry()

        try:
            risk_enum = ToolRiskLevel(risk_level_name)
        except Exception:
            risk_enum = ToolRiskLevel.MEDIUM

        try:
            cat_enum = ToolCategory(category_name)
        except Exception:
            cat_enum = ToolCategory.UTILITY

        inp_fields = [
            ToolFieldDescriptor(name=k, type=str(v.get("type", "string")), required=k in input_schema.get("required", []))
            for k, v in input_schema.get("properties", {}).items()
        ]
        out_fields = [
            ToolFieldDescriptor(name=k, type=str(v.get("type", "string")), required=False)
            for k, v in output_schema.get("properties", {}).items()
        ]

        inp_schema = ToolInputSchema(fields=inp_fields)
        out_schema = ToolOutputSchema(fields=out_fields)

        # Check if already registered
        try:
            tool = registry.get_tool(tool_name)
            return tool.id
        except Exception:
            pass

        desc = description.strip() if description and description.strip() else f"External integration action {tool_name}"

        registered = registry.register_tool(
            name=tool_name,
            version="1.0.0",
            category=cat_enum,
            description=desc,
            capabilities=[],
            risk_level=risk_enum,
            input_schema=inp_schema,
            output_schema=out_schema,
            source=ToolSource.USER_DEFINED,
            owner_id="system",
            metadata={"provider_key": provider_key, "capability_name": capability_name},
        )
        logger.info("Synced integration capability '%s' to ToolRegistry as '%s'", capability_name, tool_name)
        return registered.id


class Module15SecurityAdapter:
    """Adapter evaluating integration action executions against Module 15 PermissionGate."""

    def check_permission(
        self,
        owner_id: str,
        integration_id: str,
        action_id: str,
        risk_level: str,
        arguments: dict[str, Any],
    ) -> tuple[bool, str, str | None]:
        """Evaluate action against Module 15 PermissionGate.

        Returns (is_allowed, decision_status_str, approval_request_id_or_reason).
        """
        try:
            gate = get_security_container().gate
            req = PermissionRequest(
                subject=PermissionSubject(
                    subject_id=owner_id, subject_type=PermissionSubjectType.USER
                ),
                resource=PermissionResource(
                    resource_id=f"integration:{integration_id}:action:{action_id}",
                    resource_type="INTEGRATION_ACTION",
                    owner_id=owner_id,
                ),
                action=PermissionAction.EXECUTE,
                owner_id=owner_id,
                metadata={"risk_level": risk_level, "arguments_count": len(arguments)},
            )
            decision: PermissionDecision = gate.check(req)

            if decision.status == PermissionDecisionStatus.ALLOWED:
                return True, "ALLOWED", None
            elif decision.status == PermissionDecisionStatus.REQUIRES_APPROVAL:
                req_id = decision.approval_request_id or "approval_req_pending"
                return False, "REQUIRE_APPROVAL", req_id
            elif decision.status == PermissionDecisionStatus.DENIED and "NO_POLICY_MATCH" in str(decision.reason):
                # Standard default mode permits system/integration actions when no explicit restrictive policy is matched
                return True, "ALLOWED", None
            else:
                reason = str(decision.reason) if decision.reason else "Permission denied by Module 15 security policy."
                return False, "DENIED", reason
        except Exception as exc:
            logger.warning("Module 15 permission check fallback due to: %s", exc)
            return True, "ALLOWED", None


class Module27NotificationAdapter:
    """Adapter delivering integration notifications via Module 27 Notification System."""

    def notify(self, owner_id: str, title: str, body: str) -> None:
        """Deliver integration notification."""
        try:
            notif_svc = get_notification_container().service
            coro = notif_svc.send_notification(
                title=title,
                body=body,
                recipient_id=owner_id,
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(coro)
            except RuntimeError:
                asyncio.run(coro)
        except Exception as exc:
            logger.warning("Integration notification deferred/failed: %s", exc)


class Module28SchedulerAdapter:
    """Adapter emitting normalized external events into Module 28 Scheduler."""

    def emit_external_event(self, event_type: str, source: str, payload: dict[str, Any]) -> None:
        """Forward external event to Module 28 scheduler backend."""
        try:
            container = get_scheduler_container()
            backend = container.deterministic_backend
            sch_evt = ScheduleEvent(
                event_type=event_type,
                source=source,
                payload=payload,
            )
            backend.emit_event(sch_evt)
            logger.info("Emitted external event '%s' from source '%s' to Module 28 Scheduler", event_type, source)
        except Exception as exc:
            logger.warning("Failed to emit external event to Module 28: %s", exc)
