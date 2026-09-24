"""Tool integration for Module 24 — Document Intelligence.

Registers Document Intelligence tools with Module 14 ToolRegistry.
"""

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

DOCUMENT_TOOLS = [
    {
        "name": "document.register",
        "description": (
            "Register a document by file path or reference. Detects format via multi-signal "
            "(extension, MIME, magic bytes) and creates a tracked Document entity."
        ),
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.process",
        "description": (
            "Parse and extract full structure, metadata, and text from a registered document. "
            "Runs security inspection and creates version 1 snapshot."
        ),
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.get",
        "description": "Retrieve a Document entity by its document ID.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.list",
        "description": "List registered documents, optionally filtered by owner, type, or format.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.content",
        "description": "Read full extracted text content of a processed document.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.metadata",
        "description": "Read extracted metadata properties of a processed document.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.structure",
        "description": "Read normalized structural hierarchy of a processed document (sections, tables, headings).",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.summary",
        "description": "Get a compact summary overview of a processed document.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.search",
        "description": (
            "Perform deterministic exact-text search across one or more documents. "
            "Returns matches with citations and surrounding context windows."
        ),
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.compare",
        "description": (
            "Compute a structured machine-readable diff between two registered documents. "
            "Identifies added, removed, and modified sections."
        ),
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.validate",
        "description": "Run security and integrity validation on a registered document.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.rag.prepare",
        "description": (
            "Prepare RAG chunk candidates from a processed document for Module 10 (RAG Engine). "
            "Returns structured chunk objects with provenance metadata."
        ),
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.generate",
        "description": (
            "Generate a new document file from structured Markdown content. "
            "Supports text and Markdown output formats."
        ),
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "document.convert",
        "description": (
            "Convert a registered document from its current format to a target format. "
            "Routes through FilesystemService (M17) for write operations."
        ),
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "document.delete",
        "description": "Remove a registered document entity from the document repository.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "capabilities": [ToolCapability.WRITE_FILE],
    },
    {
        "name": "document.versions.list",
        "description": "List historical version snapshots for a document.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
    {
        "name": "document.version.get",
        "description": "Retrieve a specific document version snapshot by version ID.",
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.READ_FILE],
    },
]


def register_document_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 24 Document Intelligence tools with the ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in DOCUMENT_TOOLS:
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
