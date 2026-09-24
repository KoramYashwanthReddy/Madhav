"""In-memory repository for computer actions."""

import threading

from max.computer.domain.action import ComputerAction
from max.computer.domain.enums import ComputerActionStatus


class ComputerActionRepository:
    """In-memory repository for managing computer actions."""

    def __init__(self) -> None:
        self._actions: dict[str, ComputerAction] = {}
        self._lock = threading.RLock()

    def save(self, action: ComputerAction) -> ComputerAction:
        """Save or update an action."""
        with self._lock:
            self._actions[action.action_id] = action
            return action

    def get_by_id(self, action_id: str) -> ComputerAction | None:
        """Retrieve an action by ID."""
        with self._lock:
            return self._actions.get(action_id)

    def list_actions(
        self,
        status: ComputerActionStatus | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[ComputerAction]:
        """List actions matching optional filters."""
        with self._lock:
            results = list(self._actions.values())
            if status:
                results = [a for a in results if a.status == status]
            if agent_id:
                results = [a for a in results if a.request.agent_id == agent_id]
            # Order by request timestamp descending
            results.sort(key=lambda a: a.request.timestamp, reverse=True)
            return results[:limit]

    def clear(self) -> None:
        """Clear all stored actions."""
        with self._lock:
            self._actions.clear()
