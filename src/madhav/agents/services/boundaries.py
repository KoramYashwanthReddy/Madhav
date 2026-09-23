"""Development boundaries for Module 14 Tool Registry and Module 15 Permission Engine."""

import logging

from madhav.agents.domain.agent import PermissionRequestIntent, ToolRequestIntent

__all__ = [
    "DevPermissionGateway",
    "DevToolGateway",
    "PermissionCheckPort",
    "PermissionRequestIntent",
    "ToolExecutionGateway",
    "ToolRequestIntent",
]

logger = logging.getLogger(__name__)


class ToolExecutionGateway:
    """Null adapter boundary for Module 14 Tool Registry. DOES NOT EXECUTE TOOLS."""

    @staticmethod
    def process_tool_request(intent: ToolRequestIntent) -> ToolRequestIntent:
        """Receive tool request intent and mark boundary status (No action execution)."""
        logger.info(
            "Tool execution boundary reached (Module 14 extension point)",
            extra={
                "intent_id": intent.intent_id,
                "tool_name": intent.tool_name,
                "status": "NOT_IMPLEMENTED",
            },
        )
        # Return structured intent preserving boundary status
        return intent


class PermissionCheckPort:
    """Null adapter boundary for Module 15 Permission Engine. DOES NOT GRANT PERMISSION."""

    @staticmethod
    def check_permission(intent: PermissionRequestIntent) -> PermissionRequestIntent:
        """Receive permission request intent and mark boundary status (No permission granted)."""
        logger.info(
            "Permission boundary check reached (Module 15 extension point)",
            extra={
                "intent_id": intent.intent_id,
                "requested_permission": intent.requested_permission,
                "status": "NOT_IMPLEMENTED",
            },
        )
        # Return structured intent preserving boundary status
        return intent


DevToolGateway = ToolExecutionGateway
DevPermissionGateway = PermissionCheckPort
