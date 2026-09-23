"""Repository interfaces and in-memory implementations for Security Events and Violations."""

import threading
from abc import ABC, abstractmethod

from max.security.domain.audit import SecurityEvent, SecurityViolation
from max.security.domain.enums import SecurityEventType, SecurityViolationType


class BaseSecurityEventRepository(ABC):
    """Abstract repository for SecurityEvent persistence."""

    @abstractmethod
    def record_event(self, event: SecurityEvent) -> SecurityEvent:
        """Record an immutable security event."""
        pass

    @abstractmethod
    def get_by_id(self, event_id: str) -> SecurityEvent | None:
        """Get event by ID."""
        pass

    @abstractmethod
    def list_events(
        self,
        owner_id: str | None = None,
        event_type: SecurityEventType | None = None,
        request_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SecurityEvent], int]:
        """List audit security events."""
        pass


class BaseSecurityViolationRepository(ABC):
    """Abstract repository for SecurityViolation persistence."""

    @abstractmethod
    def record_violation(self, violation: SecurityViolation) -> SecurityViolation:
        """Record a security boundary violation."""
        pass

    @abstractmethod
    def get_by_id(self, violation_id: str) -> SecurityViolation | None:
        """Get violation by ID."""
        pass

    @abstractmethod
    def list_violations(
        self,
        owner_id: str | None = None,
        violation_type: SecurityViolationType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SecurityViolation], int]:
        """List recorded security violations."""
        pass


class InMemorySecurityEventRepository(BaseSecurityEventRepository):
    """Thread-safe in-memory security event audit repository."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: dict[str, SecurityEvent] = {}

    def record_event(self, event: SecurityEvent) -> SecurityEvent:
        with self._lock:
            self._events[event.event_id] = event
            return event

    def get_by_id(self, event_id: str) -> SecurityEvent | None:
        with self._lock:
            return self._events.get(event_id)

    def list_events(
        self,
        owner_id: str | None = None,
        event_type: SecurityEventType | None = None,
        request_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SecurityEvent], int]:
        with self._lock:
            filtered = list(self._events.values())
            if owner_id is not None:
                filtered = [e for e in filtered if e.owner_id == owner_id]
            if event_type is not None:
                filtered = [e for e in filtered if e.event_type == event_type]
            if request_id is not None:
                filtered = [e for e in filtered if e.request_id == request_id]

            filtered.sort(key=lambda e: e.timestamp, reverse=True)
            total = len(filtered)
            paginated = filtered[offset : offset + limit]
            return paginated, total


class InMemorySecurityViolationRepository(BaseSecurityViolationRepository):
    """Thread-safe in-memory security violation repository."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._violations: dict[str, SecurityViolation] = {}

    def record_violation(self, violation: SecurityViolation) -> SecurityViolation:
        with self._lock:
            self._violations[violation.violation_id] = violation
            return violation

    def get_by_id(self, violation_id: str) -> SecurityViolation | None:
        with self._lock:
            return self._violations.get(violation_id)

    def list_violations(
        self,
        owner_id: str | None = None,
        violation_type: SecurityViolationType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SecurityViolation], int]:
        with self._lock:
            filtered = list(self._violations.values())
            if owner_id is not None:
                filtered = [v for v in filtered if v.owner_id == owner_id]
            if violation_type is not None:
                filtered = [v for v in filtered if v.violation_type == violation_type]

            filtered.sort(key=lambda v: v.timestamp, reverse=True)
            total = len(filtered)
            paginated = filtered[offset : offset + limit]
            return paginated, total
