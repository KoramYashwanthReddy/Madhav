"""Tool integration for Module 27 — Notification System.

Registers controlled notification tools with Module 14 ToolRegistry.
"""

from __future__ import annotations

import logging

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

logger = logging.getLogger(__name__)

NOTIFICATION_TOOLS = [
    {
        "name": "notification.create",
        "description": "Create a new notification entity without immediately dispatching delivery.",
        "category": ToolCategory.UTILITY,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "notification.send",
        "description": "Create and immediately dispatch a notification across preferred channels.",
        "category": ToolCategory.UTILITY,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "notification.cancel",
        "description": "Cancel an active or queued notification.",
        "category": ToolCategory.UTILITY,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "notification.mark_read",
        "description": "Mark a notification as read.",
        "category": ToolCategory.UTILITY,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "notification.acknowledge",
        "description": "Record user acknowledgement for a notification.",
        "category": ToolCategory.UTILITY,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "notification.list",
        "description": "List notification history for a recipient with filters.",
        "category": ToolCategory.UTILITY,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "notification.get_preferences",
        "description": "Retrieve user notification channels and quiet hours preferences.",
        "category": ToolCategory.UTILITY,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "notification.update_preferences",
        "description": "Update user notification preference parameters.",
        "category": ToolCategory.UTILITY,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
]


def register_notification_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 27 Notification tools with the ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in NOTIFICATION_TOOLS:
        name_str: str = str(tool_def["name"])
        desc_str: str = str(tool_def["description"])
        caps: list[ToolCapability] = tool_def["capabilities"]  # type: ignore[assignment]
        risk: ToolRiskLevel = tool_def["risk_level"]  # type: ignore[assignment]
        cat: ToolCategory = tool_def["category"]  # type: ignore[assignment]

        try:
            existing, _ = tool_registry.list_tools(search_query=name_str)
            if any(t.name == name_str for t in existing):
                continue

            tool = tool_registry.register_tool(
                name=name_str,
                description=desc_str,
                version="1.0.0",
                category=cat,
                capabilities=caps,
                risk_level=risk,
                source=ToolSource.BUILT_IN,
                owner_id="system",
            )
            tool_registry.activate_tool(tool.id)
            registered_ids.append(tool.id)
        except Exception as exc:
            logger.debug("Tool '%s' registration failed or skipped: %s", name_str, exc)

    logger.info("Registered %d notification tools in ToolRegistry.", len(registered_ids))
    return registered_ids
