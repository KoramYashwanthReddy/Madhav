"""Tool integration service registering Terminal Agent tools with Module 14 ToolRegistry."""

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

TERMINAL_TOOLS = [
    {
        "name": "terminal.execute",
        "description": (
            "Execute a terminal command (PowerShell/CMD/WSL) with full security authorization. "
            "All commands are classified by risk, checked against Module 15 permission grants, "
            "and evaluated by structural command policy before execution."
        ),
        "risk_level": ToolRiskLevel.HIGH,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "terminal.execute_low_risk",
        "description": (
            "Execute a low-risk terminal command such as 'echo', 'dir', 'ls', 'pwd'. "
            "Still subject to full security authorization chain."
        ),
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "terminal.session_create",
        "description": "Create a new terminal session for a shell backend.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "terminal.session_list",
        "description": "List all active terminal sessions.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "terminal.history",
        "description": "Retrieve the command execution history for the current session.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "terminal.status",
        "description": "Return operational status of the Terminal Agent subsystem.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
]


def register_terminal_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 18 Terminal Agent tools with the ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in TERMINAL_TOOLS:
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
            category=ToolCategory.TERMINAL,
            capabilities=caps,
            risk_level=risk,
            source=ToolSource.BUILT_IN,
            owner_id="system",
        )
        tool_registry.activate_tool(tool.id)
        registered_ids.append(tool.id)

    return registered_ids
