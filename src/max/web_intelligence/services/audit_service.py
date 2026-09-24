"""AuditService for structured audit logging with secret redaction."""

from typing import Any

from max.web_intelligence.domain.models import ResearchAuditEvent
from max.web_intelligence.repositories.repositories import ResearchAuditRepository

SECRET_KEYS = {"password", "secret", "token", "api_key", "cookie", "authorization"}


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


class ResearchAuditService:
    """Logs research events with strict security redaction."""

    def __init__(self, audit_repo: ResearchAuditRepository | None = None) -> None:
        self.repo = audit_repo or ResearchAuditRepository()

    def log(
        self, research_id: str, event_type: str, owner_id: str = "system", details: dict[str, Any] | None = None
    ) -> ResearchAuditEvent:
        """Create and store a redacted ResearchAuditEvent."""
        clean_details = _redact_details(details or {})
        evt = ResearchAuditEvent(
            research_id=research_id,
            event_type=event_type,
            owner_id=owner_id,
            details=clean_details,
        )
        self.repo.log_event(evt)
        return evt
