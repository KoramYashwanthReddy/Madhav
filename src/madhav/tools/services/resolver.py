"""Tool Resolver service for resolving tool requests to verified ResolvedTool entities."""

import logging
from datetime import datetime

from madhav.tools.domain.enums import ToolCapability, ToolStatus
from madhav.tools.domain.exceptions import (
    ToolCapabilityError,
    ToolInactiveError,
    ToolNotFoundError,
)
from madhav.tools.domain.tool import ResolvedTool, Tool
from madhav.tools.repositories.tool_repository import BaseToolRepository, MemoryToolRepository
from madhav.tools.services.trace_service import ToolTraceService

logger = logging.getLogger(__name__)


class ToolResolver:
    """Resolves tool name/ID/version references to active ResolvedTool domain objects."""

    def __init__(
        self,
        tool_repository: BaseToolRepository | None = None,
        trace_service: ToolTraceService | None = None,
    ) -> None:
        self.tool_repo = tool_repository or MemoryToolRepository()
        self.trace_service = trace_service or ToolTraceService()

    def resolve_tool(
        self,
        tool_identifier: str,
        version: str | None = None,
        required_capability: ToolCapability | None = None,
    ) -> ResolvedTool:
        """Resolve a tool identifier (ID, name, or name:version) to a ResolvedTool entity."""
        tool: Tool | None = None

        # Check if tool_identifier is exact ID
        tool = self.tool_repo.get_by_id(tool_identifier)

        if not tool:
            # Check if formatted as name:version or namespace.action
            if ":" in tool_identifier:
                name, ver = tool_identifier.split(":", 1)
                tool = self.tool_repo.get_by_name_and_version(name, ver)
            elif version:
                tool = self.tool_repo.get_by_name_and_version(tool_identifier, version)
            else:
                tool = self.tool_repo.get_latest_by_name(tool_identifier)

        if not tool:
            raise ToolNotFoundError(tool_identifier)

        # Check active status
        if tool.status != ToolStatus.ACTIVE:
            raise ToolInactiveError(tool_id=tool.id, current_status=tool.status.value)

        # Check required capability if requested
        if required_capability and required_capability not in tool.capabilities:
            raise ToolCapabilityError(
                tool_id=tool.id, missing_capabilities=[required_capability.value]
            )

        resolved = ResolvedTool(
            tool_id=tool.id,
            name=tool.name,
            version=tool.version,
            tool=tool,
            is_active=True,
            resolved_at=datetime.utcnow(),
        )

        logger.debug("Tool resolved successfully", extra={"tool_id": tool.id, "tool_name": tool.name})
        return resolved
