"""SecurityModeService for managing system operational security mode state."""

import threading
from datetime import UTC, datetime

from max.security.domain.emergency import SecurityModeState
from max.security.domain.enums import SecurityEventType, SecurityMode
from max.security.services.audit_service import SecurityAuditService


class SecurityModeService:
    """Service for querying and changing system operational security mode."""

    def __init__(
        self,
        default_mode: SecurityMode = SecurityMode.NORMAL,
        audit_service: SecurityAuditService | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._audit_service = audit_service
        self._state = SecurityModeState(
            mode=default_mode,
            changed_at=datetime.now(UTC),
            changed_by="SYSTEM",
            reason="Initial default security mode",
        )

    def get_mode(self) -> SecurityModeState:
        """Get current security mode state."""
        with self._lock:
            return self._state

    def set_mode(self, mode: SecurityMode, changed_by: str, reason: str = "") -> SecurityModeState:
        """Set active security mode."""
        with self._lock:
            old_mode = self._state.mode
            now = datetime.now(UTC)
            self._state = SecurityModeState(
                mode=mode,
                changed_at=now,
                changed_by=changed_by,
                reason=reason or f"Mode transition from {old_mode.value} to {mode.value}",
            )

            if self._audit_service:
                self._audit_service.record_event(
                    event_type=SecurityEventType.SECURITY_MODE_CHANGED,
                    owner_id="system",
                    summary=f"Security mode changed from {old_mode.value} to {mode.value} by {changed_by}",
                    metadata={"old_mode": old_mode.value, "new_mode": mode.value, "reason": reason},
                )

            return self._state
