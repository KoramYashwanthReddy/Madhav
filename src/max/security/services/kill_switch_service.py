"""KillSwitchService for emergency global block activation and status."""

import threading
from datetime import UTC, datetime

from max.security.domain.emergency import EmergencyBlock
from max.security.domain.enums import SecurityEventType
from max.security.services.audit_service import SecurityAuditService


class KillSwitchService:
    """Service for activating and deactivating emergency kill-switch block."""

    def __init__(
        self,
        default_block: bool = False,
        audit_service: SecurityAuditService | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._audit_service = audit_service
        self._emergency_state = EmergencyBlock(
            enabled=default_block,
            reason="Initial state",
            activated_at=datetime.now(UTC) if default_block else None,
            activated_by="SYSTEM" if default_block else None,
        )

    def get_status(self) -> EmergencyBlock:
        """Get current emergency block status."""
        with self._lock:
            # Check if block expired
            if self._emergency_state.enabled and self._emergency_state.expires_at:
                if datetime.now(UTC) > self._emergency_state.expires_at:
                    self._emergency_state = EmergencyBlock(
                        enabled=False, reason="Emergency block expired automatically"
                    )
            return self._emergency_state

    def is_active(self) -> bool:
        """Check if emergency block is active."""
        return self.get_status().enabled

    def activate(
        self, activated_by: str, reason: str = "Emergency kill switch triggered"
    ) -> EmergencyBlock:
        """Activate emergency block immediately."""
        with self._lock:
            now = datetime.now(UTC)
            self._emergency_state = EmergencyBlock(
                enabled=True,
                reason=reason,
                activated_at=now,
                activated_by=activated_by,
            )

            if self._audit_service:
                self._audit_service.record_event(
                    event_type=SecurityEventType.EMERGENCY_BLOCK_ACTIVATED,
                    owner_id="system",
                    summary=f"Emergency block ACTIVATED by {activated_by}: {reason}",
                    metadata={"activated_by": activated_by, "reason": reason},
                )

            return self._emergency_state

    def deactivate(
        self, deactivated_by: str, reason: str = "Emergency block deactivated"
    ) -> EmergencyBlock:
        """Deactivate emergency block."""
        with self._lock:
            self._emergency_state = EmergencyBlock(
                enabled=False,
                reason=reason,
            )

            if self._audit_service:
                self._audit_service.record_event(
                    event_type=SecurityEventType.EMERGENCY_BLOCK_DEACTIVATED,
                    owner_id="system",
                    summary=f"Emergency block DEACTIVATED by {deactivated_by}: {reason}",
                    metadata={"deactivated_by": deactivated_by, "reason": reason},
                )

            return self._emergency_state
