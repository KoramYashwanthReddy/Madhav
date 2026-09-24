"""AuditService for structured audit logging with secret redaction."""

from typing import Any

from max.coding.domain.models import CodingAuditEvent
from max.coding.repositories.repositories import CodingAuditRepository

SECRET_KEYS = {"password", "secret", "token", "api_key", "cookie", "authorization", "private_key"}


def _redact_details(details: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask sensitive credentials."""
    clean: dict[str, Any] = {}
    for k, v in details.items():
        if k.lower() in SECRET_KEYS:
            clean[k] = "***REDACTED***"
        elif isinstance(v, dict):
            clean[k] = _redact_details(v)
        else:
            clean[k] = v
    return clean


class CodingAuditService:
    """Logs coding events with strict security redaction."""

    def __init__(self, audit_repo: CodingAuditRepository | None = None) -> None:
        self.repo = audit_repo or CodingAuditRepository()

    def log(
        self, session_id: str, event_type: str, owner_id: str = "system", details: dict[str, Any] | None = None
    ) -> CodingAuditEvent:
        """Create and store a redacted CodingAuditEvent."""
        clean_details = _redact_details(details or {})
        evt = CodingAuditEvent(
            session_id=session_id,
            event_type=event_type,
            owner_id=owner_id,
            details=clean_details,
        )
        self.repo.log_event(evt)
        return evt
