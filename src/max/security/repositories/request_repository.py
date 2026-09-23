"""Repository interfaces and in-memory implementations for Permission Requests and Decisions."""

import threading
from abc import ABC, abstractmethod

from max.security.domain.decision import PermissionDecision, PermissionRequest


class BasePermissionRequestRepository(ABC):
    """Abstract repository for PermissionRequest persistence."""

    @abstractmethod
    def save(self, request: PermissionRequest) -> PermissionRequest:
        """Save permission request."""
        pass

    @abstractmethod
    def get_by_id(self, request_id: str) -> PermissionRequest | None:
        """Get request by ID."""
        pass

    @abstractmethod
    def list_requests(
        self,
        owner_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PermissionRequest], int]:
        """List requests with filtering."""
        pass


class BasePermissionDecisionRepository(ABC):
    """Abstract repository for PermissionDecision persistence."""

    @abstractmethod
    def save(self, decision: PermissionDecision) -> PermissionDecision:
        """Save permission decision."""
        pass

    @abstractmethod
    def get_by_id(self, decision_id: str) -> PermissionDecision | None:
        """Get decision by ID."""
        pass

    @abstractmethod
    def get_by_request_id(self, request_id: str) -> PermissionDecision | None:
        """Get decision by request ID."""
        pass


class InMemoryPermissionRequestRepository(BasePermissionRequestRepository):
    """Thread-safe in-memory permission request repository."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._requests: dict[str, PermissionRequest] = {}

    def save(self, request: PermissionRequest) -> PermissionRequest:
        with self._lock:
            self._requests[request.request_id] = request
            return request

    def get_by_id(self, request_id: str) -> PermissionRequest | None:
        with self._lock:
            return self._requests.get(request_id)

    def list_requests(
        self,
        owner_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PermissionRequest], int]:
        with self._lock:
            filtered = list(self._requests.values())
            if owner_id is not None:
                filtered = [r for r in filtered if r.owner_id == owner_id]
            if agent_id is not None:
                filtered = [r for r in filtered if r.agent_id == agent_id]

            filtered.sort(key=lambda r: r.requested_at, reverse=True)
            total = len(filtered)
            paginated = filtered[offset : offset + limit]
            return paginated, total


class InMemoryPermissionDecisionRepository(BasePermissionDecisionRepository):
    """Thread-safe in-memory permission decision repository."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._decisions: dict[str, PermissionDecision] = {}
        self._by_request: dict[str, str] = {}

    def save(self, decision: PermissionDecision) -> PermissionDecision:
        with self._lock:
            self._decisions[decision.decision_id] = decision
            self._by_request[decision.request_id] = decision.decision_id
            return decision

    def get_by_id(self, decision_id: str) -> PermissionDecision | None:
        with self._lock:
            return self._decisions.get(decision_id)

    def get_by_request_id(self, request_id: str) -> PermissionDecision | None:
        with self._lock:
            decision_id = self._by_request.get(request_id)
            if decision_id:
                return self._decisions.get(decision_id)
            return None
