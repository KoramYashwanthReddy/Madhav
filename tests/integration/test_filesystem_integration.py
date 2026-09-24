"""Integration tests for Module 17 Filesystem Agent, ToolRegistry, and Security container."""

import pytest

from max.filesystem.container import get_filesystem_container, reset_filesystem_container
from max.filesystem.services.tool_integration import register_filesystem_tools
from max.security.container import reset_security_container
from max.tools.services.registry import ToolRegistryService


@pytest.fixture(autouse=True)
def reset_containers():
    """Reset dependency containers before and after tests."""
    reset_filesystem_container()
    reset_security_container()
    yield
    reset_filesystem_container()
    reset_security_container()


def test_tool_registry_registration_integration():
    """Verify filesystem tools are registered into ToolRegistry."""
    tool_registry = ToolRegistryService(auto_load_dev_tools=False)
    registered_ids = register_filesystem_tools(tool_registry)

    assert len(registered_ids) == 15
    tools, count = tool_registry.list_tools(search_query="filesystem")
    assert count == 15

    tool_names = [t.name for t in tools]
    assert "filesystem.read" in tool_names
    assert "filesystem.write" in tool_names
    assert "filesystem.delete" in tool_names
    assert "filesystem.search" in tool_names


def test_filesystem_container_initialization():
    """Verify FilesystemContainer initializes with mock backend and path security."""
    container = get_filesystem_container(use_mock_backend=True)
    status = container.filesystem_service.get_status()

    assert status["enabled"] is True
    assert status["backend_type"] == "MockFilesystemBackend"
    assert "filesystem_read" in [c.lower() for c in status["capabilities"]]
