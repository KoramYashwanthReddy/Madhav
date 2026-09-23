"""Tool Registry and lifecycle management service."""

import logging
from datetime import datetime
from typing import Any

from max.config.sections import ToolRegistrySettings
from max.tools.domain.enums import (
    ToolAvailabilityStatus,
    ToolCapability,
    ToolCategory,
    ToolEventType,
    ToolRiskLevel,
    ToolSource,
    ToolStatus,
)
from max.tools.domain.exceptions import (
    DuplicateToolError,
    InvalidToolDefinitionError,
    ToolNotFoundError,
)
from max.tools.domain.tool import (
    Tool,
    ToolAvailability,
    ToolConfiguration,
    ToolInputSchema,
    ToolOutputSchema,
)
from max.tools.providers.dev_tools import DevToolsProvider
from max.tools.repositories.tool_repository import BaseToolRepository, MemoryToolRepository
from max.tools.services.trace_service import ToolTraceService

logger = logging.getLogger(__name__)


class ToolStateTransitionValidator:
    """Validates state machine transitions for registered tools."""

    VALID_TRANSITIONS: dict[ToolStatus, set[ToolStatus]] = {
        ToolStatus.REGISTERED: {ToolStatus.ACTIVE, ToolStatus.DISABLED},
        ToolStatus.ACTIVE: {ToolStatus.DISABLED, ToolStatus.DEPRECATED, ToolStatus.ARCHIVED},
        ToolStatus.DISABLED: {ToolStatus.ACTIVE, ToolStatus.ARCHIVED},
        ToolStatus.DEPRECATED: {ToolStatus.ARCHIVED},
        ToolStatus.ARCHIVED: set(),  # Terminal state
    }

    @classmethod
    def validate_transition(cls, current: ToolStatus, target: ToolStatus, tool_name: str) -> None:
        """Enforce state machine rules."""
        if current == target:
            return
        allowed = cls.VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidToolDefinitionError(
                f"Cannot transition tool '{tool_name}' status from '{current.value}' to '{target.value}'."
            )


class ToolRegistryService:
    """Service managing Tool definitions, registration, lifecycle state transitions, and updates."""

    def __init__(
        self,
        tool_repository: BaseToolRepository | None = None,
        trace_service: ToolTraceService | None = None,
        settings: ToolRegistrySettings | None = None,
        auto_load_dev_tools: bool = True,
    ) -> None:
        self.tool_repo = tool_repository or MemoryToolRepository()
        self.trace_service = trace_service or ToolTraceService()
        self.settings = settings or ToolRegistrySettings()

        if auto_load_dev_tools and self.settings.allow_development_tools:
            self._load_default_dev_tools()

    @property
    def repository(self) -> BaseToolRepository:
        return self.tool_repo

    def _load_default_dev_tools(self) -> None:
        """Pre-populate safe default development tools if not present."""
        for dev_tool in DevToolsProvider.get_default_development_tools():
            existing = self.tool_repo.get_by_name_and_version(dev_tool.name, dev_tool.version)
            if not existing:
                self.tool_repo.save(dev_tool)

    def register_tool(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        category: ToolCategory = ToolCategory.UTILITY,
        capabilities: list[ToolCapability] | None = None,
        risk_level: ToolRiskLevel = ToolRiskLevel.LOW,
        source: ToolSource = ToolSource.USER_DEFINED,
        input_schema: ToolInputSchema | None = None,
        output_schema: ToolOutputSchema | None = None,
        configuration: ToolConfiguration | None = None,
        owner_id: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> Tool:
        """Register a new Tool definition."""
        existing = self.tool_repo.get_by_name_and_version(name, version)
        if existing:
            raise DuplicateToolError(name, version)

        tool = Tool(
            name=name,
            version=version,
            description=description,
            category=category,
            capabilities=capabilities or [ToolCapability.TEXT_TRANSFORMATION],
            status=ToolStatus.REGISTERED,
            risk_level=risk_level,
            source=source,
            input_schema=input_schema or ToolInputSchema(),
            output_schema=output_schema or ToolOutputSchema(),
            configuration=configuration or ToolConfiguration(),
            owner_id=owner_id,
            metadata=metadata or {},
        )
        saved = self.tool_repo.save(tool)

        self.trace_service.record_event(
            event_type=ToolEventType.TOOL_REGISTERED,
            tool_id=saved.id,
            summary=f"Tool '{saved.name}' version '{saved.version}' registered with category '{saved.category.value}'",
            metadata={"owner_id": owner_id},
        )

        logger.info(
            "Tool registered",
            extra={"tool_id": saved.id, "tool_name": saved.name, "version": saved.version},
        )
        return saved

    def get_tool(self, tool_id: str) -> Tool:
        """Retrieve tool definition by ID."""
        tool = self.tool_repo.get_by_id(tool_id)
        if not tool:
            raise ToolNotFoundError(tool_id)
        return tool

    def update_tool(
        self,
        tool_id: str,
        description: str | None = None,
        category: ToolCategory | None = None,
        capabilities: list[ToolCapability] | None = None,
        risk_level: ToolRiskLevel | None = None,
        configuration: ToolConfiguration | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Tool:
        """Update properties of an existing tool."""
        tool = self.get_tool(tool_id)
        updated_dict = tool.model_dump()

        if description is not None:
            updated_dict["description"] = description
        if category is not None:
            updated_dict["category"] = category
        if capabilities is not None:
            updated_dict["capabilities"] = capabilities
        if risk_level is not None:
            updated_dict["risk_level"] = risk_level
        if configuration is not None:
            updated_dict["configuration"] = configuration
        if metadata is not None:
            merged_meta = dict(tool.metadata)
            merged_meta.update(metadata)
            updated_dict["metadata"] = merged_meta

        updated_dict["updated_at"] = datetime.utcnow()
        new_tool = Tool(**updated_dict)
        return self.tool_repo.save(new_tool)

    def transition_tool_status(
        self, tool_id: str, target_status: ToolStatus, reason: str = "Status update"
    ) -> Tool:
        """Transition tool lifecycle status."""
        tool = self.get_tool(tool_id)
        ToolStateTransitionValidator.validate_transition(tool.status, target_status, tool.name)

        avail_status = (
            ToolAvailabilityStatus.AVAILABLE
            if target_status == ToolStatus.ACTIVE
            else ToolAvailabilityStatus.DISABLED
        )

        updated_dict = tool.model_dump()
        updated_dict["status"] = target_status
        updated_dict["availability"] = ToolAvailability(
            status=avail_status,
            is_available=(target_status == ToolStatus.ACTIVE),
            reason=reason,
        )
        updated_dict["updated_at"] = datetime.utcnow()

        saved = self.tool_repo.save(Tool(**updated_dict))

        event_map = {
            ToolStatus.ACTIVE: ToolEventType.TOOL_ACTIVATED,
            ToolStatus.DISABLED: ToolEventType.TOOL_DISABLED,
            ToolStatus.DEPRECATED: ToolEventType.TOOL_DEPRECATED,
            ToolStatus.ARCHIVED: ToolEventType.TOOL_ARCHIVED,
        }
        event_type = event_map.get(target_status, ToolEventType.TOOL_ACTIVATED)

        self.trace_service.record_event(
            event_type=event_type,
            tool_id=saved.id,
            summary=f"Tool '{saved.name}' status transitioned to '{target_status.value}' ({reason})",
        )
        return saved

    def activate_tool(self, tool_id: str) -> Tool:
        return self.transition_tool_status(tool_id, ToolStatus.ACTIVE, reason="Activated")

    def disable_tool(self, tool_id: str) -> Tool:
        return self.transition_tool_status(tool_id, ToolStatus.DISABLED, reason="Disabled")

    def deprecate_tool(self, tool_id: str) -> Tool:
        return self.transition_tool_status(tool_id, ToolStatus.DEPRECATED, reason="Deprecated")

    def archive_tool(self, tool_id: str) -> Tool:
        return self.transition_tool_status(tool_id, ToolStatus.ARCHIVED, reason="Archived")

    def delete_tool(self, tool_id: str) -> bool:
        self.archive_tool(tool_id)
        return self.tool_repo.delete(tool_id)

    def list_tools(
        self,
        category: ToolCategory | None = None,
        capability: ToolCapability | None = None,
        status: ToolStatus | None = None,
        search_query: str | None = None,
        owner_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Tool], int]:
        """List tool definitions with filtering and pagination."""
        effective_limit = min(limit, self.settings.max_page_size)
        return self.tool_repo.list_tools(
            category=category,
            capability=capability,
            status=status,
            search_query=search_query,
            owner_id=owner_id,
            limit=effective_limit,
            offset=offset,
        )


ToolRegistry = ToolRegistryService
ToolRegistrationService = ToolRegistryService
