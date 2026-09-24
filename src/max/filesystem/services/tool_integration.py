"""Tool integration service registering Filesystem Agent tools into Module 14 ToolRegistry."""


from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

FILESYSTEM_TOOLS = [
    {
        "name": "filesystem.exists",
        "description": "Check whether a file or directory exists at the given path.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "filesystem.stat",
        "description": "Inspect detailed metadata of a file or directory.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "filesystem.list",
        "description": "List directory entries and metadata.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "filesystem.read",
        "description": "Read text or binary file contents safely with size limits.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "filesystem.write",
        "description": "Write text or binary content to a file (supports atomic write).",
        "risk_level": ToolRiskLevel.HIGH,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "filesystem.append",
        "description": "Append content to an existing file.",
        "risk_level": ToolRiskLevel.HIGH,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "filesystem.create",
        "description": "Create a new file at specified path.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "filesystem.mkdir",
        "description": "Create a directory structure.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "filesystem.copy",
        "description": "Copy a file or directory to destination.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.READ_FILE, ToolCapability.WRITE_FILE],
    },
    {
        "name": "filesystem.move",
        "description": "Move a file or directory to a new destination.",
        "risk_level": ToolRiskLevel.HIGH,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "filesystem.rename",
        "description": "Rename a file or directory within authorized boundaries.",
        "risk_level": ToolRiskLevel.HIGH,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "filesystem.delete",
        "description": "Delete a file or directory safely with explicit safeguards.",
        "risk_level": ToolRiskLevel.HIGH,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "filesystem.search",
        "description": "Search filesystem recursively matching patterns within limits.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "filesystem.hash",
        "description": "Calculate cryptographic hash (SHA-256) of a file.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "filesystem.compare",
        "description": "Compare two files by size, hash, and content.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
]


def register_filesystem_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 17 Filesystem Agent tools with ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in FILESYSTEM_TOOLS:
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
            category=ToolCategory.FILESYSTEM,
            capabilities=caps,
            risk_level=risk,
            source=ToolSource.BUILT_IN,
            owner_id="system",
        )
        tool_registry.activate_tool(tool.id)
        registered_ids.append(tool.id)

    return registered_ids
