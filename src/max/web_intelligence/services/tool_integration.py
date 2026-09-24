"""Tool integration service registering Module 21 Web Intelligence tools with Module 14 ToolRegistry."""

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

WEB_INTELLIGENCE_TOOLS = [
    {
        "name": "web.search",
        "description": "Perform web search for candidate sources matching a query.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "web.research",
        "description": "Initiate structured, multi-step web research pipeline.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "web.source.inspect",
        "description": "Inspect candidate source metadata, freshness, and authority.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "web.extract",
        "description": "Extract structured evidence claims from acquired web content.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "web.compare",
        "description": "Compare claims across sources to detect agreements and conflicts.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "web.citations",
        "description": "Generate and validate first-class citations for research output.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "web.fact_check",
        "description": "Execute structured fact-check workflow for a candidate statement.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "web.research.status",
        "description": "Retrieve current operational status of an active research request.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
]


def register_web_intelligence_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 21 Web Intelligence tools with the ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in WEB_INTELLIGENCE_TOOLS:
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
            category=ToolCategory.UTILITY,
            capabilities=caps,
            risk_level=risk,
            source=ToolSource.BUILT_IN,
            owner_id="system",
        )
        tool_registry.activate_tool(tool.id)
        registered_ids.append(tool.id)

    return registered_ids
