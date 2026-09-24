"""Tool integration service registering Application Control tools with Module 14 ToolRegistry."""

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

APPLICATION_TOOLS = [
    {
        "name": "app.list",
        "description": "List applications discovered on the system or filter by category/installed status.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "app.launch",
        "description": "Launch an application by ID, display name, or executable with optional arguments.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "app.focus",
        "description": "Bring an application window to the foreground.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "app.close",
        "description": "Gracefully close or terminate an application instance.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "app.restart",
        "description": "Restart an application instance.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "app.get_windows",
        "description": "Get all open window handles, titles, and positions for an application.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "app.get_status",
        "description": "Get real-time status and resource utilization (CPU, memory, uptime) for an application.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
]


def register_application_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 19 Application Control tools with the ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in APPLICATION_TOOLS:
        name_str: str = str(tool_def["name"])
        desc_str: str = str(tool_def["description"])
        caps: list[ToolCapability] = tool_def["capabilities"]  # type: ignore[assignment]
        risk: ToolRiskLevel = tool_def["risk_level"]  # type: ignore[assignment]

        existing, _ = tool_registry.list_tools(search_query=name_str)
        if any(t.name == name_str for t in existing):
            continue

        tool = tool_registry.register_tool(
            name=name_str,
            description=desc_str,
            version="1.0.0",
            category=ToolCategory.APPLICATION,
            capabilities=caps,
            risk_level=risk,
            source=ToolSource.BUILT_IN,
            owner_id="system",
        )
        tool_registry.activate_tool(tool.id)
        registered_ids.append(tool.id)

    return registered_ids
