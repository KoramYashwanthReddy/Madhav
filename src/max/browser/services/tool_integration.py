"""Tool integration service registering Browser Agent tools with Module 14 ToolRegistry."""

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

BROWSER_TOOLS = [
    {
        "name": "browser.session.create",
        "description": "Create a new isolated browser session.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.session.close",
        "description": "Close an active browser session.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.tab.list",
        "description": "List open tabs in a browser session.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.tab.create",
        "description": "Create a new tab in a browser session.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.tab.switch",
        "description": "Switch active tab in a browser session.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.tab.close",
        "description": "Close a tab in a browser session.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.navigate",
        "description": "Navigate a browser tab to a specified URL.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.OPEN_BROWSER, ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "browser.back",
        "description": "Navigate back in browser tab history.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.forward",
        "description": "Navigate forward in browser tab history.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.reload",
        "description": "Reload the current page in a browser tab.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.observe",
        "description": "Extract structured observation of current page state.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "browser.click",
        "description": "Click an interactive element on the page.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.CLICK_BROWSER],
    },
    {
        "name": "browser.type",
        "description": "Type text into an input element.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.TYPE_BROWSER],
    },
    {
        "name": "browser.select",
        "description": "Select an option from a select dropdown.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.CLICK_BROWSER],
    },
    {
        "name": "browser.scroll",
        "description": "Scroll page in a specified direction.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.wait",
        "description": "Wait for element or condition on page.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.OPEN_BROWSER],
    },
    {
        "name": "browser.screenshot",
        "description": "Capture page screenshot.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "browser.extract_text",
        "description": "Extract visible text content from page.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "browser.extract_links",
        "description": "Extract links from current page.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "browser.extract_forms",
        "description": "Extract form elements and structure from page.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "browser.download",
        "description": "Download a file from page through safe path validation.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.READ_WEB_PAGE],
    },
    {
        "name": "browser.upload",
        "description": "Upload a file into a browser form element.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.TYPE_BROWSER],
    },
]


def register_browser_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 20 Browser Agent tools with the ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in BROWSER_TOOLS:
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
            category=ToolCategory.BROWSER,
            capabilities=caps,
            risk_level=risk,
            source=ToolSource.BUILT_IN,
            owner_id="system",
        )
        tool_registry.activate_tool(tool.id)
        registered_ids.append(tool.id)

    return registered_ids
