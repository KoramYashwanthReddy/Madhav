"""Module 14 Tool Registry integration for computer control tools."""

import logging

from max.tools.domain.enums import (
    ToolCategory,
    ToolRiskLevel,
    ToolSource,
    ToolStatus,
)
from max.tools.domain.tool import (
    Tool,
    ToolFieldDescriptor,
    ToolInputSchema,
)
from max.tools.services.registry import ToolRegistryService

logger = logging.getLogger(__name__)


def create_computer_control_tools() -> list[Tool]:
    """Build tool definitions for all Module 16 computer control capabilities."""
    tools: list[Tool] = [
        # Screen capture
        Tool(
            name="computer.screen_capture",
            version="1.0.0",
            description="Capture full screen, specific monitor display, or bounded rectangular screen region.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="display_id", type="string", required=False, description="Display ID (default: display_0)"),
                    ToolFieldDescriptor(name="region", type="object", required=False, description="Optional bounding box {x, y, width, height}"),
                ]
            ),
        ),
        # Screen info
        Tool(
            name="computer.get_screen_info",
            version="1.0.0",
            description="Retrieve information on connected displays, dimensions, resolution, and DPI scaling.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
        ),
        # Cursor pos
        Tool(
            name="computer.get_cursor_position",
            version="1.0.0",
            description="Get current mouse cursor screen coordinates (x, y).",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
        ),
        # Move mouse
        Tool(
            name="computer.move_mouse",
            version="1.0.0",
            description="Move mouse cursor to target screen coordinates (x, y).",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="x", type="integer", required=True, description="Target X coordinate"),
                    ToolFieldDescriptor(name="y", type="integer", required=True, description="Target Y coordinate"),
                    ToolFieldDescriptor(name="duration", type="number", required=False, description="Movement duration in seconds"),
                ]
            ),
        ),
        # Click mouse
        Tool(
            name="computer.click_mouse",
            version="1.0.0",
            description="Click mouse button at optional target screen coordinates.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="x", type="integer", required=False, description="Optional target X coordinate"),
                    ToolFieldDescriptor(name="y", type="integer", required=False, description="Optional target Y coordinate"),
                    ToolFieldDescriptor(name="button", type="string", required=False, description="Mouse button (left, right, middle)"),
                    ToolFieldDescriptor(name="click_count", type="integer", required=False, description="Number of clicks"),
                ]
            ),
        ),
        # Double click
        Tool(
            name="computer.double_click",
            version="1.0.0",
            description="Double-click mouse button at optional target screen coordinates.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="x", type="integer", required=False, description="Optional target X coordinate"),
                    ToolFieldDescriptor(name="y", type="integer", required=False, description="Optional target Y coordinate"),
                    ToolFieldDescriptor(name="button", type="string", required=False, description="Mouse button (left, right, middle)"),
                ]
            ),
        ),
        # Drag mouse
        Tool(
            name="computer.drag_mouse",
            version="1.0.0",
            description="Perform click-and-drag mouse operation from start to end coordinates.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.HIGH,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="start_x", type="integer", required=True, description="Start X coordinate"),
                    ToolFieldDescriptor(name="start_y", type="integer", required=True, description="Start Y coordinate"),
                    ToolFieldDescriptor(name="end_x", type="integer", required=True, description="End X coordinate"),
                    ToolFieldDescriptor(name="end_y", type="integer", required=True, description="End Y coordinate"),
                    ToolFieldDescriptor(name="duration", type="number", required=False, description="Drag duration in seconds"),
                    ToolFieldDescriptor(name="button", type="string", required=False, description="Mouse button (left, right, middle)"),
                ]
            ),
        ),
        # Scroll
        Tool(
            name="computer.scroll",
            version="1.0.0",
            description="Scroll mouse wheel vertically or horizontally.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="clicks", type="integer", required=True, description="Scroll amount/clicks (positive=up, negative=down)"),
                    ToolFieldDescriptor(name="direction", type="string", required=False, description="Scroll direction ('vertical', 'horizontal')"),
                    ToolFieldDescriptor(name="x", type="integer", required=False, description="Optional pointer X coordinate"),
                    ToolFieldDescriptor(name="y", type="integer", required=False, description="Optional pointer Y coordinate"),
                ]
            ),
        ),
        # Press key
        Tool(
            name="computer.press_key",
            version="1.0.0",
            description="Press a keyboard key with optional key modifiers.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="key", type="string", required=True, description="Target keyboard key identifier"),
                    ToolFieldDescriptor(name="modifiers", type="array", required=False, description="List of modifier keys ('ctrl', 'alt', 'shift', 'win')"),
                ]
            ),
        ),
        # Type text
        Tool(
            name="computer.type_text",
            version="1.0.0",
            description="Type text sequence into active focused application window.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.HIGH,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="text", type="string", required=True, description="Text string to type"),
                    ToolFieldDescriptor(name="interval", type="number", required=False, description="Typing delay interval between characters"),
                ]
            ),
        ),
        # Keyboard shortcut
        Tool(
            name="computer.keyboard_shortcut",
            version="1.0.0",
            description="Trigger keyboard shortcut combination (e.g. ['ctrl', 'c']).",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.HIGH,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="keys", type="array", required=True, description="Key combination array"),
                ]
            ),
        ),
        # Get active window
        Tool(
            name="computer.get_active_window",
            version="1.0.0",
            description="Get currently focused foreground application window information.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
        ),
        # List windows
        Tool(
            name="computer.list_windows",
            version="1.0.0",
            description="List open GUI windows on system with optional filters.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="visible_only", type="boolean", required=False, description="Filter for visible windows only"),
                    ToolFieldDescriptor(name="title_filter", type="string", required=False, description="Filter windows by title substring"),
                    ToolFieldDescriptor(name="app_filter", type="string", required=False, description="Filter windows by app identifier"),
                ]
            ),
        ),
        # Focus window
        Tool(
            name="computer.focus_window",
            version="1.0.0",
            description="Bring target application window to foreground focus.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="window_id", type="string", required=True, description="Target window identifier"),
                ]
            ),
        ),
        # Minimize window
        Tool(
            name="computer.minimize_window",
            version="1.0.0",
            description="Minimize target window.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="window_id", type="string", required=True, description="Target window identifier"),
                ]
            ),
        ),
        # Maximize window
        Tool(
            name="computer.maximize_window",
            version="1.0.0",
            description="Maximize target window.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="window_id", type="string", required=True, description="Target window identifier"),
                ]
            ),
        ),
        # Restore window
        Tool(
            name="computer.restore_window",
            version="1.0.0",
            description="Restore window from minimized/maximized state.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="window_id", type="string", required=True, description="Target window identifier"),
                ]
            ),
        ),
        # Move window
        Tool(
            name="computer.move_window",
            version="1.0.0",
            description="Move window to target screen coordinates (x, y).",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="window_id", type="string", required=True, description="Target window identifier"),
                    ToolFieldDescriptor(name="x", type="integer", required=True, description="New X coordinate"),
                    ToolFieldDescriptor(name="y", type="integer", required=True, description="New Y coordinate"),
                ]
            ),
        ),
        # Resize window
        Tool(
            name="computer.resize_window",
            version="1.0.0",
            description="Resize window to specified width and height.",
            category=ToolCategory.SYSTEM,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.BUILT_IN,
            status=ToolStatus.ACTIVE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(name="window_id", type="string", required=True, description="Target window identifier"),
                    ToolFieldDescriptor(name="width", type="integer", required=True, description="New width in pixels"),
                    ToolFieldDescriptor(name="height", type="integer", required=True, description="New height in pixels"),
                ]
            ),
        ),
    ]
    return tools


def register_computer_control_tools(registry_service: ToolRegistryService) -> list[Tool]:
    """Register all computer control tools with Module 14 ToolRegistry."""
    tools = create_computer_control_tools()
    registered: list[Tool] = []
    for tool in tools:
        try:
            reg_tool = registry_service.register_tool(
                name=tool.name,
                description=tool.description,
                version=tool.version,
                category=tool.category,
                risk_level=tool.risk_level,
                source=tool.source,
                input_schema=tool.input_schema,
                output_schema=tool.output_schema,
            )
            registered.append(reg_tool)
        except Exception as exc:
            logger.warning("Computer tool registration skipped or updated for '%s': %s", tool.name, exc)
    return registered
