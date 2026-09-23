"""Safe, deterministic in-memory development tools provider for Module 14."""

from typing import Any

from max.tools.domain.enums import (
    ToolCapability,
    ToolCategory,
    ToolRiskLevel,
    ToolSource,
    ToolStatus,
)
from max.tools.domain.exceptions import ToolError, ToolExecutionBoundaryError
from max.tools.domain.tool import (
    Tool,
    ToolFieldDescriptor,
    ToolInputSchema,
    ToolOutputSchema,
)


class DevToolsProvider:
    """Provides pure in-memory development tools and non-executable future tool definitions."""

    @staticmethod
    def get_default_development_tools() -> list[Tool]:
        """Return default pre-registered safe development tools and future stub definitions."""
        return [
            DevToolsProvider.create_echo_tool(),
            DevToolsProvider.create_math_tool(),
            DevToolsProvider.create_text_tool(),
            DevToolsProvider.create_future_terminal_stub(),
            DevToolsProvider.create_future_filesystem_stub(),
            DevToolsProvider.create_future_browser_stub(),
        ]

    @staticmethod
    def create_echo_tool() -> Tool:
        """Create echo.test development tool definition."""
        return Tool(
            id="echo.test:v1",
            name="echo.test",
            version="1.0.0",
            description="Pure in-memory test tool that echoes input message",
            category=ToolCategory.UTILITY,
            capabilities=[ToolCapability.ECHO_TEST, ToolCapability.TEXT_TRANSFORMATION],
            status=ToolStatus.ACTIVE,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.DEVELOPMENT,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="message",
                        type="string",
                        required=True,
                        description="Message text to echo",
                    )
                ]
            ),
            output_schema=ToolOutputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="message",
                        type="string",
                        required=True,
                        description="Echoed message text",
                    )
                ]
            ),
        )

    @staticmethod
    def create_math_tool() -> Tool:
        """Create math.calculate development tool definition."""
        return Tool(
            id="math.calculate:v1",
            name="math.calculate",
            version="1.0.0",
            description="Safe in-memory arithmetic calculator tool (add, subtract, multiply, divide)",
            category=ToolCategory.UTILITY,
            capabilities=[ToolCapability.MATH_CALCULATION],
            status=ToolStatus.ACTIVE,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.DEVELOPMENT,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="operation",
                        type="string",
                        required=True,
                        allowed_values=["add", "subtract", "multiply", "divide"],
                        description="Arithmetic operation",
                    ),
                    ToolFieldDescriptor(
                        name="left",
                        type="number",
                        required=True,
                        description="Left numeric operand",
                    ),
                    ToolFieldDescriptor(
                        name="right",
                        type="number",
                        required=True,
                        description="Right numeric operand",
                    ),
                ]
            ),
            output_schema=ToolOutputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="result",
                        type="number",
                        required=True,
                        description="Calculated numeric result",
                    )
                ]
            ),
        )

    @staticmethod
    def create_text_tool() -> Tool:
        """Create text.transform development tool definition."""
        return Tool(
            id="text.transform:v1",
            name="text.transform",
            version="1.0.0",
            description="Safe in-memory string transformer tool (uppercase, lowercase, trim)",
            category=ToolCategory.UTILITY,
            capabilities=[ToolCapability.TEXT_TRANSFORMATION],
            status=ToolStatus.ACTIVE,
            risk_level=ToolRiskLevel.LOW,
            source=ToolSource.DEVELOPMENT,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="operation",
                        type="string",
                        required=True,
                        allowed_values=["uppercase", "lowercase", "trim"],
                        description="String operation",
                    ),
                    ToolFieldDescriptor(
                        name="text", type="string", required=True, description="Input string text"
                    ),
                ]
            ),
            output_schema=ToolOutputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="result",
                        type="string",
                        required=True,
                        description="Transformed string result",
                    )
                ]
            ),
        )

    @staticmethod
    def create_future_terminal_stub() -> Tool:
        """Create terminal.execute future high-risk tool definition (non-executable in Module 14)."""
        return Tool(
            id="terminal.execute:v1",
            name="terminal.execute",
            version="1.0.0",
            description="Future system terminal command execution tool (NON-EXECUTEABLE in Module 14)",
            category=ToolCategory.TERMINAL,
            capabilities=[ToolCapability.EXECUTE_COMMAND],
            status=ToolStatus.DISABLED,
            risk_level=ToolRiskLevel.CRITICAL,
            source=ToolSource.FUTURE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="command",
                        type="string",
                        required=True,
                        description="Terminal command string",
                    )
                ]
            ),
            output_schema=ToolOutputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="exit_code",
                        type="integer",
                        required=True,
                        description="Command exit code",
                    ),
                    ToolFieldDescriptor(
                        name="output",
                        type="string",
                        required=True,
                        description="Standard output text",
                    ),
                ]
            ),
        )

    @staticmethod
    def create_future_filesystem_stub() -> Tool:
        """Create filesystem.write future high-risk tool definition (non-executable in Module 14)."""
        return Tool(
            id="filesystem.write:v1",
            name="filesystem.write",
            version="1.0.0",
            description="Future filesystem write tool (NON-EXECUTEABLE in Module 14)",
            category=ToolCategory.FILESYSTEM,
            capabilities=[ToolCapability.WRITE_FILE],
            status=ToolStatus.DISABLED,
            risk_level=ToolRiskLevel.HIGH,
            source=ToolSource.FUTURE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="path", type="string", required=True, description="Target file path"
                    ),
                    ToolFieldDescriptor(
                        name="content",
                        type="string",
                        required=True,
                        description="Content text to write",
                    ),
                ]
            ),
            output_schema=ToolOutputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="bytes_written",
                        type="integer",
                        required=True,
                        description="Number of bytes written",
                    )
                ]
            ),
        )

    @staticmethod
    def create_future_browser_stub() -> Tool:
        """Create browser.open future tool definition (non-executable in Module 14)."""
        return Tool(
            id="browser.open:v1",
            name="browser.open",
            version="1.0.0",
            description="Future web browser open URL tool (NON-EXECUTEABLE in Module 14)",
            category=ToolCategory.BROWSER,
            capabilities=[ToolCapability.OPEN_BROWSER],
            status=ToolStatus.DISABLED,
            risk_level=ToolRiskLevel.MEDIUM,
            source=ToolSource.FUTURE,
            input_schema=ToolInputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="url", type="string", required=True, description="Target URL string"
                    )
                ]
            ),
            output_schema=ToolOutputSchema(
                fields=[
                    ToolFieldDescriptor(
                        name="title", type="string", required=True, description="Opened page title"
                    )
                ]
            ),
        )

    @staticmethod
    def execute_dev_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute pure in-memory development operations. Raise ToolError if invalid or division by zero."""
        if tool_name == "echo.test":
            return {"message": str(arguments.get("message", ""))}

        elif tool_name == "math.calculate":
            op = arguments.get("operation")
            left = float(arguments.get("left", 0))
            right = float(arguments.get("right", 0))

            if op == "add":
                res = left + right
            elif op == "subtract":
                res = left - right
            elif op == "multiply":
                res = left * right
            elif op == "divide":
                if right == 0:
                    raise ToolError("Division by zero error in math.calculate")
                res = left / right
            else:
                raise ToolError(f"Unsupported math operation '{op}'")

            return {"result": float(res)}

        elif tool_name == "text.transform":
            op = arguments.get("operation")
            text = str(arguments.get("text", ""))

            if op == "uppercase":
                text_res = text.upper()
            elif op == "lowercase":
                text_res = text.lower()
            elif op == "trim":
                text_res = text.strip()
            else:
                raise ToolError(f"Unsupported text operation '{op}'")

            return {"result": text_res}

        else:
            raise ToolExecutionBoundaryError(
                tool_id=tool_name,
                boundary_reason=f"Tool '{tool_name}' is not an executable development tool.",
            )
