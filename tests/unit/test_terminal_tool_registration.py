"""Unit tests for Module 18 Terminal Agent tool registration with ToolRegistry."""

import pytest

from max.terminal.services.tool_integration import TERMINAL_TOOLS, register_terminal_tools
from max.tools.services.registry import ToolRegistryService


@pytest.fixture
def tool_registry() -> ToolRegistryService:
    """Tool registry without pre-loaded dev tools (avoids FUTURE stub conflicts)."""
    return ToolRegistryService(auto_load_dev_tools=False)


class TestTerminalToolRegistration:
    def test_register_all_terminal_tools(self, tool_registry):
        registered_ids = register_terminal_tools(tool_registry)
        assert len(registered_ids) == len(TERMINAL_TOOLS)

    def test_tool_names_match_spec(self, tool_registry):
        register_terminal_tools(tool_registry)
        tools, _ = tool_registry.list_tools()
        tool_names = {t.name for t in tools}
        for tool_def in TERMINAL_TOOLS:
            assert tool_def["name"] in tool_names

    def test_terminal_execute_is_registered(self, tool_registry):
        register_terminal_tools(tool_registry)
        tools, _ = tool_registry.list_tools(search_query="terminal.execute")
        assert any(t.name == "terminal.execute" for t in tools)

    def test_tools_are_active_after_registration(self, tool_registry):
        register_terminal_tools(tool_registry)
        tools, _ = tool_registry.list_tools()
        terminal_tools = [t for t in tools if t.name.startswith("terminal.")]
        from max.tools.domain.enums import ToolStatus
        for tool in terminal_tools:
            assert tool.status == ToolStatus.ACTIVE

    def test_idempotent_registration(self, tool_registry):
        """Registering the same tools twice must not create duplicates."""
        ids_first = register_terminal_tools(tool_registry)
        ids_second = register_terminal_tools(tool_registry)
        assert len(ids_second) == 0  # Second call returns empty (already registered)

        tools, _ = tool_registry.list_tools()
        terminal_tools = [t for t in tools if t.name.startswith("terminal.")]
        assert len(terminal_tools) == len(TERMINAL_TOOLS)

    def test_terminal_execute_is_high_risk(self, tool_registry):
        register_terminal_tools(tool_registry)
        tools, _ = tool_registry.list_tools(search_query="terminal.execute")
        execute_tool = next(t for t in tools if t.name == "terminal.execute")
        from max.tools.domain.enums import ToolRiskLevel
        assert execute_tool.risk_level == ToolRiskLevel.HIGH

    def test_terminal_status_is_low_risk(self, tool_registry):
        register_terminal_tools(tool_registry)
        tools, _ = tool_registry.list_tools(search_query="terminal.status")
        status_tool = next(t for t in tools if t.name == "terminal.status")
        from max.tools.domain.enums import ToolRiskLevel
        assert status_tool.risk_level == ToolRiskLevel.LOW

    def test_tools_have_execute_command_capability(self, tool_registry):
        register_terminal_tools(tool_registry)
        tools, _ = tool_registry.list_tools()
        terminal_tools = [t for t in tools if t.name.startswith("terminal.")]
        from max.tools.domain.enums import ToolCapability
        for tool in terminal_tools:
            assert ToolCapability.EXECUTE_COMMAND in tool.capabilities
