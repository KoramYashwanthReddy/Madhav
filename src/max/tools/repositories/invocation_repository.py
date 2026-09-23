"""Tool invocations repository interfaces and thread-safe in-memory implementation."""

import threading
from abc import ABC, abstractmethod

from max.tools.domain.enums import ToolInvocationStatus
from max.tools.domain.invocation import ToolInvocation


class BaseToolInvocationRepository(ABC):
    """Abstract base repository for ToolInvocation entities."""

    @abstractmethod
    def save(self, invocation: ToolInvocation) -> ToolInvocation:
        """Save or update a tool invocation record."""
        pass

    @abstractmethod
    def get_by_id(self, invocation_id: str) -> ToolInvocation | None:
        """Retrieve invocation by ID."""
        pass

    @abstractmethod
    def get_by_client_request_id(self, client_request_id: str) -> ToolInvocation | None:
        """Retrieve invocation by idempotency key."""
        pass

    @abstractmethod
    def list_invocations(
        self,
        tool_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
        status: ToolInvocationStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ToolInvocation], int]:
        """List tool invocations with filtering and pagination."""
        pass

    @abstractmethod
    def delete(self, invocation_id: str) -> bool:
        """Delete an invocation record."""
        pass


class InMemoryToolInvocationRepository(BaseToolInvocationRepository):
    """Thread-safe in-memory repository implementation for ToolInvocations."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._invocations: dict[str, ToolInvocation] = {}

    def save(self, invocation: ToolInvocation) -> ToolInvocation:
        with self._lock:
            self._invocations[invocation.invocation_id] = invocation
            return invocation

    def get_by_id(self, invocation_id: str) -> ToolInvocation | None:
        with self._lock:
            return self._invocations.get(invocation_id)

    def get_by_client_request_id(self, client_request_id: str) -> ToolInvocation | None:
        with self._lock:
            for inv in self._invocations.values():
                if inv.client_request_id == client_request_id:
                    return inv
            return None

    def list_invocations(
        self,
        tool_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
        status: ToolInvocationStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ToolInvocation], int]:
        with self._lock:
            results = list(self._invocations.values())

            if tool_id is not None:
                results = [i for i in results if i.tool_id == tool_id]
            if agent_id is not None:
                results = [i for i in results if i.context.agent_id == agent_id]
            if run_id is not None:
                results = [i for i in results if i.context.run_id == run_id]
            if task_id is not None:
                results = [i for i in results if i.context.task_id == task_id]
            if status is not None:
                results = [i for i in results if i.status == status]

            results.sort(key=lambda x: x.created_at, reverse=True)
            total = len(results)
            paged = results[offset : offset + limit]
            return paged, total

    def delete(self, invocation_id: str) -> bool:
        with self._lock:
            if invocation_id in self._invocations:
                del self._invocations[invocation_id]
                return True
            return False


MemoryToolInvocationRepository = InMemoryToolInvocationRepository
