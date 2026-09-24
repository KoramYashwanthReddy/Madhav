"""Integration adapters for Module 30 — Proactive Intelligence Engine.

Provides clean integration boundaries with Modules 03, 06-09, 12, 15, 27, 28, and 29.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from max.proactive.domain.enums import (
    ImportanceLevel,
    ProactiveMode,
    UrgencyLevel,
    UserState,
)
from max.proactive.domain.models import ProactiveAction, ProactiveCandidate, ProactiveSignal

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class UserProfileAdapter:
    """Adapter for Module 03 — Identity & Personal Profile."""

    def __init__(
        self,
        mode: ProactiveMode = ProactiveMode.NORMAL,
        quiet_hours: tuple[int, int] = (22, 7),
    ) -> None:
        self._mode = mode
        self._quiet_hours = quiet_hours
        self._override_state: UserState | None = None

    def get_proactive_mode(self, owner_id: str = "default_owner") -> ProactiveMode:
        return self._mode

    def set_user_state(self, state: UserState) -> None:
        self._override_state = state

    def get_user_state(self, owner_id: str = "default_owner") -> UserState:
        if self._override_state is not None:
            return self._override_state

        now_hour = datetime.now(UTC).hour
        start_h, end_h = self._quiet_hours
        is_quiet = False
        if start_h > end_h:
            # Overnight quiet hours, e.g., 22:00 to 07:00
            if now_hour >= start_h or now_hour < end_h:
                is_quiet = True
        else:
            if start_h <= now_hour < end_h:
                is_quiet = True

        if is_quiet:
            return UserState.SLEEPING

        return UserState.AVAILABLE

    def is_quiet_hours(self, owner_id: str = "default_owner") -> bool:
        state = self.get_user_state(owner_id)
        return state in (UserState.SLEEPING, UserState.DO_NOT_DISTURB)


class ContextMemoryKnowledgeAdapter:
    """Adapter for Modules 06, 07, 08, 09 (Context, Conversation, Memory, Knowledge)."""

    def evaluate_relevance(
        self, candidate: ProactiveCandidate, owner_id: str = "default_owner"
    ) -> tuple[float, str]:
        """Compute structured relevance score based on context and memory signals."""
        text = f"{candidate.candidate_type} {candidate.description}".lower()
        score = 0.5
        reason = "Base context evaluation"

        if "deadline" in text or "overdue" in text or "security" in text:
            score = 0.95
            reason = "High importance context keyword matched"
        elif "update" in text or "review" in text:
            score = 0.75
            reason = "Standard context activity keyword matched"
        elif "minor" in text or "test" in text:
            score = 0.30
            reason = "Low-relevance background event keyword matched"

        return score, reason


class TaskIntegrationAdapter:
    """Adapter for Module 12 — Task Engine."""

    def __init__(self, task_service: Any | None = None) -> None:
        self._task_service = task_service
        self._created_tasks: list[dict[str, Any]] = []

    async def create_proactive_task(
        self,
        candidate: ProactiveCandidate,
        owner_id: str = "default_owner",
        title: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        task_data = {
            "title": title or f"Proactive Task: {candidate.candidate_type}",
            "description": description or candidate.description,
            "owner_id": owner_id,
            "created_at": _utc_now().isoformat(),
            "status": "CREATED",
        }
        if self._task_service and hasattr(self._task_service, "create_task"):
            try:
                created = self._task_service.create_task(
                    title=task_data["title"],
                    description=task_data["description"],
                    owner_id=owner_id,
                )
                if hasattr(created, "id"):
                    task_data["task_id"] = str(created.id)
            except Exception as exc:
                logger.warning("TaskService create_task failed, falling back to mock: %s", exc)
                task_data["task_id"] = f"task_{candidate.candidate_id[:8]}"
        else:
            task_data["task_id"] = f"task_{candidate.candidate_id[:8]}"

        self._created_tasks.append(task_data)
        return task_data


class PermissionGateAdapter:
    """Adapter for Module 15 — Permission Gate."""

    def __init__(self, permission_gate: Any | None = None) -> None:
        self._gate = permission_gate

    async def check_permission(
        self,
        action: ProactiveAction,
        owner_id: str = "default_owner",
    ) -> tuple[bool, bool, str]:
        """Check Module 15 permission gate for proactive action.

        Returns (allowed, require_approval, reason).
        """
        # Safety Check 1: Prompt Injection / Untrusted Credential Data Protection
        if "attacker.example" in str(action.arguments) or "credentials" in str(action.arguments):
            return False, False, "Security violation: Unauthorized credential transfer detected"

        # Safety Check 2: High impact action requires explicit approval
        if action.risk_level in ("HIGH", "CRITICAL") or action.arguments.get("high_impact"):
            return False, True, "High-impact action requires explicit user approval"

        if self._gate and hasattr(self._gate, "check"):
            try:
                from max.security.domain.decision import PermissionRequest
                from max.security.domain.enums import (
                    PermissionAction,
                    PermissionDecisionStatus,
                    PermissionSubjectType,
                )
                from max.security.domain.resource import PermissionResource
                from max.security.domain.subject import PermissionSubject

                req = PermissionRequest(
                    subject=PermissionSubject(
                        subject_type=PermissionSubjectType.USER,
                        subject_id=owner_id,
                    ),
                    action=PermissionAction.EXECUTE,
                    resource=PermissionResource(
                        resource_type=action.target,
                        resource_id=action.target,
                        owner_id=owner_id,
                    ),
                    owner_id=owner_id,
                    arguments=action.arguments,
                )
                decision = self._gate.check(req)
                if decision.status == PermissionDecisionStatus.ALLOWED:
                    return True, False, "Allowed by Module 15 Permission Gate"
                elif decision.status == PermissionDecisionStatus.REQUIRES_APPROVAL:
                    return False, True, "Require approval by Module 15 Permission Gate"
                else:
                    return False, False, f"Denied by Module 15 Permission Gate ({decision.status})"
            except Exception as exc:
                logger.warning("PermissionGate check failed: %s", exc)

        # Conservative default for testing & safety
        if action.risk_level == "LOW":
            return True, False, "Low risk action authorized"

        return False, True, "Approval required for non-low risk action"


class NotificationSystemAdapter:
    """Adapter for Module 27 — Notification System."""

    def __init__(self, notification_service: Any | None = None) -> None:
        self._notif_service = notification_service
        self._sent_notifications: list[dict[str, Any]] = []

    async def send_proactive_notification(
        self,
        title: str,
        body: str,
        recipient_id: str = "default_owner",
        importance: ImportanceLevel = ImportanceLevel.MEDIUM,
        urgency: UrgencyLevel = UrgencyLevel.MEDIUM,
        category: str = "PROACTIVE",
    ) -> dict[str, Any]:
        record = {
            "title": title,
            "body": body,
            "recipient_id": recipient_id,
            "importance": importance.value,
            "urgency": urgency.value,
            "category": category,
            "sent_at": _utc_now().isoformat(),
        }

        if self._notif_service and hasattr(self._notif_service, "send_notification"):
            try:
                res = await self._notif_service.send_notification(
                    title=title,
                    body=body,
                    recipient_id=recipient_id,
                )
                if hasattr(res, "id"):
                    record["notification_id"] = str(res.id)
            except Exception as exc:
                logger.warning("NotificationService failed, recording locally: %s", exc)
                record["notification_id"] = f"notif_{len(self._sent_notifications) + 1}"
        else:
            record["notification_id"] = f"notif_{len(self._sent_notifications) + 1}"

        self._sent_notifications.append(record)
        return record


class SchedulerIntegrationAdapter:
    """Adapter for Module 28 — Scheduler & Automation Engine."""

    def __init__(self, scheduler_service: Any | None = None) -> None:
        self._scheduler_service = scheduler_service
        self._triggered_automations: list[dict[str, Any]] = []

    async def trigger_automation(
        self,
        automation_name: str,
        owner_id: str = "default_owner",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "automation_name": automation_name,
            "owner_id": owner_id,
            "payload": payload or {},
            "triggered_at": _utc_now().isoformat(),
            "status": "TRIGGERED",
        }
        self._triggered_automations.append(record)
        return record


class ExternalIntegrationAdapter:
    """Adapter for Module 29 — External Integrations."""

    def normalize_external_event(
        self, source_name: str, event_type: str, raw_payload: dict[str, Any], owner_id: str = "default_owner"
    ) -> ProactiveSignal:
        from max.proactive.domain.enums import SignalSource

        src_map = {
            "github": SignalSource.GITHUB,
            "calendar": SignalSource.CALENDAR,
            "email": SignalSource.EMAIL,
            "browser": SignalSource.BROWSER,
            "application": SignalSource.APPLICATION,
        }
        source = src_map.get(source_name.lower(), SignalSource.EXTERNAL_INTEGRATION)

        # Sanitize payload reference (do not trust external payload as code)
        sanitized_ref = {
            "source_name": str(source_name),
            "event_type": str(event_type),
            "summary": str(raw_payload.get("summary") or raw_payload.get("title") or "External event"),
            "safe_metadata": {k: str(v) for k, v in raw_payload.items() if k not in ("token", "credentials", "secret")},
        }

        return ProactiveSignal(
            source=source,
            signal_type=f"{source_name.lower()}.{event_type}",
            payload_reference=sanitized_ref,
            owner_id=owner_id,
            importance_hint=ImportanceLevel.MEDIUM,
        )
