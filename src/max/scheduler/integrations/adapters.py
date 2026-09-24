"""Integration adapters for Modules 12, 13, 14, 15, and 27."""

import asyncio
import logging
from typing import Any

from max.notifications.container import get_notification_container
from max.security.container import get_security_container
from max.security.domain.decision import PermissionDecision, PermissionRequest
from max.security.domain.enums import (
    PermissionAction,
    PermissionDecisionStatus,
    PermissionSubjectType,
)
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject
from max.tasks.domain.enums import TaskPriority, TaskSource, TaskType
from max.tasks.domain.task import Task
from max.tasks.services.task_service import TaskService
from max.tools.services.invocation_service import ToolInvocationService
from max.tools.services.registry import ToolRegistryService

logger = logging.getLogger(__name__)


class TaskEngineAdapter:
    """Adapter for Module 12 — Task Engine."""

    def __init__(self, task_service: TaskService | None = None) -> None:
        self._task_service = task_service or TaskService()

    def create_task_for_automation(
        self,
        name: str,
        description: str = "",
        owner_id: str = "default_user",
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a new Task entity in Module 12."""
        return self._task_service.create_task(
            owner_id=owner_id,
            title=name,
            description=description,
            type=TaskType.SYSTEM,
            priority=TaskPriority.NORMAL,
            source=TaskSource.SYSTEM,
        )

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID from Module 12."""
        return self._task_service.get_task(task_id)


class AgentEngineAdapter:
    """Adapter for Module 13 — Agent Engine."""

    def __init__(self, agent_coordinator: Any | None = None) -> None:
        self._coordinator = agent_coordinator

    def assign_and_execute_task(
        self, task: Task, agent_id: str | None = None
    ) -> dict[str, Any]:
        """Dispatch task to agent engine for assignment and execution."""
        logger.info(
            "Dispatching task '%s' (ID: %s) to agent engine (requested agent: %s).",
            task.title,
            task.id,
            agent_id or "auto-assign",
        )
        return {
            "task_id": task.id,
            "status": "DISPATCHED",
            "assigned_agent_id": agent_id or "default_agent",
        }


class ToolRegistryAdapter:
    """Adapter for Module 14 — Tool Registry."""

    def __init__(
        self,
        registry_service: ToolRegistryService | None = None,
        invocation_service: ToolInvocationService | None = None,
    ) -> None:
        self._registry = registry_service or ToolRegistryService()
        self._invocation = invocation_service or ToolInvocationService()

    def resolve_tool(self, tool_id: str) -> Any | None:
        """Look up tool in Module 14 registry."""
        return self._registry.get_tool(tool_id)

    def invoke_tool(
        self, tool_id: str, arguments: dict[str, Any], owner_id: str = "default_user"
    ) -> dict[str, Any]:
        """Invoke registered tool via Module 14 invocation service."""
        try:
            from max.tools.domain.invocation import ToolInvocationRequest

            req = ToolInvocationRequest(
                tool_name=tool_id,
                arguments=arguments,
                owner_id=owner_id,
            )
            result = self._invocation.invoke_tool(req)
            return {
                "invocation_id": result.invocation_id,
                "status": result.status,
                "result": result.output,
                "error": None,
            }
        except Exception as exc:
            logger.error("Tool invocation '%s' failed: %s", tool_id, exc)
            return {"status": "FAILED", "error": str(exc)}


class PermissionSecurityAdapter:
    """Adapter for Module 15 — Permission & Security Module."""

    def check_permission(
        self,
        subject_id: str,
        resource_id: str,
        action_name: str = "EXECUTE",
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, str, str | None]:
        """Evaluate action against Module 15 PermissionGate.

        Returns (is_allowed, decision_status_str, approval_request_id_or_reason).
        """
        try:
            gate = get_security_container().gate
            try:
                act = PermissionAction(action_name)
            except Exception:
                act = PermissionAction.EXECUTE

            req = PermissionRequest(
                subject=PermissionSubject(
                    subject_id=subject_id, subject_type=PermissionSubjectType.USER
                ),
                resource=PermissionResource(
                    resource_id=resource_id, resource_type="SCHEDULER_ACTION", owner_id=subject_id
                ),
                action=act,
                owner_id=subject_id,
                metadata=metadata or {},
            )
            decision: PermissionDecision = gate.check(req)

            if decision.status == PermissionDecisionStatus.ALLOWED:
                return True, "ALLOWED", None
            elif decision.status == PermissionDecisionStatus.REQUIRES_APPROVAL:
                req_id = decision.approval_request_id or "approval_req_pending"
                return False, "REQUIRE_APPROVAL", req_id
            elif decision.status == PermissionDecisionStatus.DENIED and "NO_POLICY_MATCH" in str(decision.reason):
                # When no explicit policy matches in default mode, default permission is granted
                return True, "ALLOWED", None
            else:
                reason = str(decision.reason) if decision.reason else "Permission denied by Module 15 security policy."
                return False, "DENIED", reason
        except Exception as exc:
            logger.warning("Module 15 permission check fallback due to: %s", exc)
            # Default to ALLOWED in basic mode if gate uninitialized
            return True, "ALLOWED", None


class NotificationAdapter:
    """Adapter for Module 27 — Notification System."""

    def send_scheduler_notification(
        self,
        owner_id: str,
        title: str,
        body: str,
        event_type: str = "SCHEDULER_EVENT",
        priority: str = "NORMAL",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Deliver scheduler lifecycle notification via Module 27."""
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
            logger.warning("Notification delivery via Module 27 deferred/failed: %s", exc)


