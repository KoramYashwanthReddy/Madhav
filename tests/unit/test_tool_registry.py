"""Unit tests for ToolRegistryService, discovery, resolution, and lifecycle state transitions."""

import pytest

from madhav.tools.domain.enums import ToolCapability, ToolCategory, ToolStatus
from madhav.tools.domain.exceptions import (
    DuplicateToolError,
    InvalidToolDefinitionError,
    ToolInactiveError,
    ToolNotFoundError,
)
from madhav.tools.repositories.tool_repository import InMemoryToolRepository
from madhav.tools.services.discovery_service import ToolDiscoveryService
from madhav.tools.services.registry import ToolRegistryService
from madhav.tools.services.resolver import ToolResolver


@pytest.fixture
def repo():
    return InMemoryToolRepository()


@pytest.fixture
def registry_service(repo):
    return ToolRegistryService(tool_repository=repo, auto_load_dev_tools=True)


@pytest.fixture
def discovery_service(repo):
    return ToolDiscoveryService(tool_repository=repo)


@pytest.fixture
def resolver(repo):
    return ToolResolver(tool_repository=repo)


def test_tool_registry_crud_and_lifecycle(registry_service) -> None:
    """Test tool registration, retrieval, status state machine transitions, and duplicate prevention."""
    tool = registry_service.register_tool(
        name="custom.formatter",
        description="Formats string output",
        category=ToolCategory.UTILITY,
        capabilities=[ToolCapability.TEXT_TRANSFORMATION],
    )
    assert tool.status == ToolStatus.REGISTERED

    # Duplicate registration fails
    with pytest.raises(DuplicateToolError):
        registry_service.register_tool(
            name="custom.formatter",
            description="Duplicate tool",
            version="1.0.0",
        )

    # Activate tool
    active_tool = registry_service.activate_tool(tool.id)
    assert active_tool.status == ToolStatus.ACTIVE
    assert active_tool.availability.is_available is True

    # Disable tool
    disabled_tool = registry_service.disable_tool(tool.id)
    assert disabled_tool.status == ToolStatus.DISABLED
    assert disabled_tool.availability.is_available is False

    # Invalid state transition (DISABLED -> DEPRECATED directly is invalid)
    with pytest.raises(InvalidToolDefinitionError):
        registry_service.deprecate_tool(tool.id)

    # Reactivate then deprecate
    registry_service.activate_tool(tool.id)
    deprecated = registry_service.deprecate_tool(tool.id)
    assert deprecated.status == ToolStatus.DEPRECATED

    # Archive tool
    archived = registry_service.archive_tool(tool.id)
    assert archived.status == ToolStatus.ARCHIVED


def test_tool_discovery_and_resolution(registry_service, discovery_service, resolver) -> None:
    """Test tool discovery by capability and resolution by name."""
    # Discover default echo.test tool preloaded
    echo_tools = discovery_service.discover_tools_for_capability(ToolCapability.ECHO_TEST)
    assert len(echo_tools) >= 1
    assert echo_tools[0].name == "echo.test"

    # Resolve active tool
    resolved = resolver.resolve_tool("echo.test")
    assert resolved.is_active is True
    assert resolved.name == "echo.test"

    # Nonexistent tool resolution fails
    with pytest.raises(ToolNotFoundError):
        resolver.resolve_tool("nonexistent.tool")

    # Disabled tool resolution fails
    registry_service.disable_tool(echo_tools[0].id)
    with pytest.raises(ToolInactiveError):
        resolver.resolve_tool("echo.test")
