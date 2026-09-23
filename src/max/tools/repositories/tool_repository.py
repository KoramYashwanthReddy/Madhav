"""Tool definitions repository interfaces and thread-safe in-memory implementation."""

import threading
from abc import ABC, abstractmethod

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolStatus
from max.tools.domain.tool import Tool


class BaseToolRepository(ABC):
    """Abstract base repository for Tool definitions persistence."""

    @abstractmethod
    def save(self, tool: Tool) -> Tool:
        """Save or update a tool definition."""
        pass

    @abstractmethod
    def get_by_id(self, tool_id: str) -> Tool | None:
        """Retrieve tool by ID."""
        pass

    @abstractmethod
    def get_by_name_and_version(self, name: str, version: str) -> Tool | None:
        """Retrieve tool by exact name and version."""
        pass

    @abstractmethod
    def get_latest_by_name(self, name: str) -> Tool | None:
        """Retrieve latest active or registered version of a tool by name."""
        pass

    @abstractmethod
    def list_tools(
        self,
        category: ToolCategory | None = None,
        capability: ToolCapability | None = None,
        status: ToolStatus | None = None,
        search_query: str | None = None,
        owner_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Tool], int]:
        """List and search tools with filtering and pagination."""
        pass

    @abstractmethod
    def delete(self, tool_id: str) -> bool:
        """Remove tool record by ID."""
        pass


class InMemoryToolRepository(BaseToolRepository):
    """Thread-safe in-memory repository implementation for Tools."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tools: dict[str, Tool] = {}

    def save(self, tool: Tool) -> Tool:
        with self._lock:
            self._tools[tool.id] = tool
            return tool

    def get_by_id(self, tool_id: str) -> Tool | None:
        with self._lock:
            return self._tools.get(tool_id)

    def get_by_name_and_version(self, name: str, version: str) -> Tool | None:
        with self._lock:
            for tool in self._tools.values():
                if tool.name == name and tool.version == version:
                    return tool
            return None

    def get_latest_by_name(self, name: str) -> Tool | None:
        with self._lock:
            matches = [
                t
                for t in self._tools.values()
                if t.name == name and t.status != ToolStatus.ARCHIVED
            ]
            if not matches:
                return None
            # Sort by version descending (basic string comparison or semantic version)
            matches.sort(key=lambda x: x.version, reverse=True)
            return matches[0]

    def list_tools(
        self,
        category: ToolCategory | None = None,
        capability: ToolCapability | None = None,
        status: ToolStatus | None = None,
        search_query: str | None = None,
        owner_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Tool], int]:
        with self._lock:
            results = list(self._tools.values())

            if category is not None:
                results = [t for t in results if t.category == category]
            if capability is not None:
                results = [t for t in results if capability in t.capabilities]
            if status is not None:
                results = [t for t in results if t.status == status]
            if owner_id is not None:
                results = [t for t in results if t.owner_id == owner_id]
            if search_query is not None and search_query.strip():
                query = search_query.lower().strip()
                results = [
                    t for t in results if query in t.name.lower() or query in t.description.lower()
                ]

            results.sort(key=lambda x: x.created_at, reverse=True)
            total = len(results)
            paged = results[offset : offset + limit]
            return paged, total

    def delete(self, tool_id: str) -> bool:
        with self._lock:
            if tool_id in self._tools:
                del self._tools[tool_id]
                return True
            return False


MemoryToolRepository = InMemoryToolRepository
