"""Module 15 Permission and Module 16+ Execution boundary interfaces and development adapters."""

import logging
from typing import Any

from madhav.tools.domain.enums import ToolRiskLevel, ToolSource
from madhav.tools.domain.exceptions import ToolExecutionBoundaryError, ToolPermissionRequiredError
from madhav.tools.domain.invocation import ToolInvocation
from madhav.tools.domain.tool import Tool
from madhav.tools.providers.dev_tools import DevToolsProvider

logger = logging.getLogger(__name__)


class PermissionCheckPort:
    """Boundary interface for Module 15 Permission & Security Engine. DOES NOT GRANT PERMISSIONS AUTOMATICALLY."""

    @staticmethod
    def check_permission(tool: Tool, invocation: ToolInvocation) -> dict[str, Any]:
        """Inspect whether tool invocation has required permissions."""
        logger.info(
            "Permission boundary check (Module 15 extension point)",
            extra={
                "tool_id": tool.id,
                "tool_name": tool.name,
                "risk_level": tool.risk_level.value,
                "invocation_id": invocation.invocation_id,
            },
        )

        # High/Critical risk tools terminate at Permission boundary
        if tool.risk_level in (ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL):
            raise ToolPermissionRequiredError(
                tool_id=tool.id,
                permission_name=f"permission.{tool.category.value.lower()}.{tool.name}",
            )

        return {
            "permitted": True,
            "boundary": "DEVELOPMENT_PERMITTED",
            "reason": f"Tool '{tool.name}' (risk: {tool.risk_level.value}) allowed for development invocation.",
        }


class ToolExecutionPort:
    """Boundary interface for Module 16+ Execution Layer. Routes dev tools safely, terminates real-world system calls."""

    @staticmethod
    def execute(tool: Tool, invocation: ToolInvocation) -> dict[str, Any]:
        """Execute tool invocation through controlled boundary."""
        logger.info(
            "Tool execution boundary reached",
            extra={
                "tool_id": tool.id,
                "tool_name": tool.name,
                "source": tool.source.value,
                "invocation_id": invocation.invocation_id,
            },
        )

        # Development tools run in-memory
        if tool.source == ToolSource.DEVELOPMENT:
            return DevToolsProvider.execute_dev_tool(tool.name, invocation.arguments)

        # Built-in or future system tools terminate at Execution boundary
        raise ToolExecutionBoundaryError(
            tool_id=tool.id,
            boundary_reason=f"Execution layer (Module 16+) not implemented for '{tool.name}' (Source: {tool.source.value}).",
        )


DevPermissionGateway = PermissionCheckPort
DevToolExecutionGateway = ToolExecutionPort
