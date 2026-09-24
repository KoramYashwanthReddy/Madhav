"""Tool integration service registering Module 22 Coding Agent tools with Module 14 ToolRegistry."""

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

CODING_TOOLS = [
    {
        "name": "coding.repository.inspect",
        "description": "Inspect repository structure, project type, and metadata.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.file.read",
        "description": "Read file content or line range from software repository.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.code.search",
        "description": "Search code repository for matching text patterns.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.symbol.search",
        "description": "Search repository for classes, functions, and symbol definitions.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.analyze",
        "description": "Perform static analysis and dependency graph extraction.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.plan",
        "description": "Generate structured implementation plan for a coding task.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.patch.preview",
        "description": "Preview unified diff representation of proposed code patch.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.patch.apply",
        "description": "Apply targeted patch changeset to repository files.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "coding.test",
        "description": "Execute unit or integration test suite.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "coding.build",
        "description": "Execute project compilation or build check.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "coding.lint",
        "description": "Execute linter to check code style and formatting issues.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "coding.typecheck",
        "description": "Execute static type checker to verify code types.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "coding.debug",
        "description": "Analyze test or build failure output and diagnose root cause.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.review",
        "description": "Perform automated code quality and security review.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.diff",
        "description": "Compute diff comparison between file versions.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "coding.validate",
        "description": "Run complete validation pipeline (build, lint, typecheck, tests).",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.EXECUTE_COMMAND],
    },
    {
        "name": "coding.explain",
        "description": "Generate structural explanation of a code file or component.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
]


def register_coding_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 22 Coding Agent tools with the ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in CODING_TOOLS:
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
