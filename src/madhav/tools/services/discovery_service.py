"""Tool Discovery Service for capability filtering and AI agent context descriptors."""

import logging

from madhav.tools.domain.enums import ToolCapability, ToolCategory, ToolStatus
from madhav.tools.domain.tool import Tool, ToolDescriptor
from madhav.tools.repositories.tool_repository import BaseToolRepository, MemoryToolRepository

logger = logging.getLogger(__name__)


class ToolDiscoveryService:
    """Service for discovering, searching, and producing compact AI tool descriptors."""

    def __init__(self, tool_repository: BaseToolRepository | None = None) -> None:
        self.tool_repo = tool_repository or MemoryToolRepository()

    def discover_tools_for_capability(
        self, capability: ToolCapability, active_only: bool = True
    ) -> list[Tool]:
        """Find registered tools supporting a specific capability."""
        status_filter = ToolStatus.ACTIVE if active_only else None
        tools, _ = self.tool_repo.list_tools(capability=capability, status=status_filter, limit=100)
        return tools

    def discover_descriptors_for_capabilities(
        self, required_capabilities: list[ToolCapability], active_only: bool = True
    ) -> list[ToolDescriptor]:
        """Produce compact descriptors of active tools matching any of the required capabilities."""
        status_filter = ToolStatus.ACTIVE if active_only else None
        descriptors: list[ToolDescriptor] = []
        seen_ids: set[str] = set()

        for cap in required_capabilities:
            tools, _ = self.tool_repo.list_tools(capability=cap, status=status_filter, limit=100)
            for tool in tools:
                if tool.id not in seen_ids:
                    seen_ids.add(tool.id)
                    descriptors.append(tool.to_descriptor())

        return descriptors

    def search_tools(
        self,
        category: ToolCategory | None = None,
        capability: ToolCapability | None = None,
        query: str | None = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ToolDescriptor], int]:
        """Search available tools and return compact descriptors."""
        status_filter = ToolStatus.ACTIVE if active_only else None
        tools, total = self.tool_repo.list_tools(
            category=category,
            capability=capability,
            status=status_filter,
            search_query=query,
            limit=limit,
            offset=offset,
        )
        return [t.to_descriptor() for t in tools], total

    def get_all_active_descriptors(self) -> list[ToolDescriptor]:
        """Retrieve compact descriptors for all currently ACTIVE tools."""
        tools, _ = self.tool_repo.list_tools(status=ToolStatus.ACTIVE, limit=500)
        return [t.to_descriptor() for t in tools]
