"""Repository interface and in-memory implementation for ApprovalRequests."""

import threading
from abc import ABC, abstractmethod

from max.security.domain.approval import ApprovalRequest
from max.security.domain.enums import ApprovalStatus


class BaseApprovalRepository(ABC):
    """Abstract repository interface for ApprovalRequest persistence."""

    @abstractmethod
    def save(self, approval: ApprovalRequest) -> ApprovalRequest:
        """Save or update approval request."""
        pass

    @abstractmethod
    def get_by_id(self, approval_id: str) -> ApprovalRequest | None:
        """Get approval request by ID."""
        pass

    @abstractmethod
    def get_by_permission_request_id(self, permission_request_id: str) -> ApprovalRequest | None:
        """Get approval request by permission request ID."""
        pass

    @abstractmethod
    def list_approvals(
        self,
        owner_id: str | None = None,
        status: ApprovalStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ApprovalRequest], int]:
        """List approval requests with filtering and pagination."""
        pass


class InMemoryApprovalRepository(BaseApprovalRepository):
    """Thread-safe in-memory approval repository."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._approvals: dict[str, ApprovalRequest] = {}
        self._by_permission_req: dict[str, str] = {}

    def save(self, approval: ApprovalRequest) -> ApprovalRequest:
        with self._lock:
            self._approvals[approval.approval_id] = approval
            self._by_permission_req[approval.permission_request_id] = approval.approval_id
            return approval

    def get_by_id(self, approval_id: str) -> ApprovalRequest | None:
        with self._lock:
            return self._approvals.get(approval_id)

    def get_by_permission_request_id(self, permission_request_id: str) -> ApprovalRequest | None:
        with self._lock:
            appr_id = self._by_permission_req.get(permission_request_id)
            if appr_id:
                return self._approvals.get(appr_id)
            return None

    def list_approvals(
        self,
        owner_id: str | None = None,
        status: ApprovalStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ApprovalRequest], int]:
        with self._lock:
            filtered = list(self._approvals.values())
            if owner_id is not None:
                filtered = [a for a in filtered if a.owner_id == owner_id]
            if status is not None:
                filtered = [a for a in filtered if a.status == status]

            filtered.sort(key=lambda a: a.created_at, reverse=True)
            total = len(filtered)
            paginated = filtered[offset : offset + limit]
            return paginated, total
