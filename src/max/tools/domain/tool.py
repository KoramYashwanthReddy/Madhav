"""Tool domain models, schemas, descriptor, and configuration."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from max.tools.domain.enums import (
    ToolAvailabilityStatus,
    ToolCapability,
    ToolCategory,
    ToolRiskLevel,
    ToolSource,
    ToolStatus,
)
from max.tools.domain.exceptions import InvalidToolDefinitionError


class ToolFieldDescriptor(BaseModel):
    """Description of a single input or output argument property."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Property field key")
    type: str = Field(default="string", description="JSON/Python data type string")
    required: bool = Field(default=True, description="Whether property is mandatory")
    description: str = Field(default="", description="Human-readable field description")
    allowed_values: list[Any] | None = Field(default=None, description="Enumerated permitted values")
    min_length: int | None = Field(default=None, description="Minimum string length")
    max_length: int | None = Field(default=None, description="Maximum string length")
    min_value: float | None = Field(default=None, description="Minimum numeric bound")
    max_value: float | None = Field(default=None, description="Maximum numeric bound")


class ToolInputSchema(BaseModel):
    """Structured input argument specification for a tool."""

    model_config = ConfigDict(frozen=True)

    fields: list[ToolFieldDescriptor] = Field(default_factory=list, description="Argument descriptors")
    allow_additional_properties: bool = Field(default=False, description="Allow undeclared arguments")

    def get_required_field_names(self) -> list[str]:
        return [f.name for f in self.fields if f.required]

    def get_field_map(self) -> dict[str, ToolFieldDescriptor]:
        return {f.name: f for f in self.fields}


class ToolOutputSchema(BaseModel):
    """Structured output result specification for a tool."""

    model_config = ConfigDict(frozen=True)

    fields: list[ToolFieldDescriptor] = Field(default_factory=list, description="Output properties descriptors")
    description: str = Field(default="Tool execution result schema", description="Output schema description")


class ToolConfiguration(BaseModel):
    """Configurable operational controls for a tool."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = Field(default=True, description="Enable state")
    timeout_seconds: float = Field(default=30.0, ge=0.1, description="Execution timeout limit")
    max_input_size_bytes: int = Field(default=1048576, description="Max input payload size")
    max_output_size_bytes: int = Field(default=5242880, description="Max output payload size")
    version_policy: str = Field(default="STRICT", description="Schema version enforcement policy")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom configuration key-values")


class ToolAvailability(BaseModel):
    """Operational capability availability check descriptor."""

    model_config = ConfigDict(frozen=True)

    status: ToolAvailabilityStatus = Field(default=ToolAvailabilityStatus.AVAILABLE, description="Availability state")
    is_available: bool = Field(default=True, description="Available flag")
    reason: str = Field(default="Tool is operational", description="Reason text")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last status check timestamp")


class ToolDescriptor(BaseModel):
    """Compact descriptor of a tool prepared for AI agent model context insertion."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Unique tool ID")
    name: str = Field(description="Deterministic tool name")
    version: str = Field(description="Semantic version string")
    category: ToolCategory = Field(description="Tool category taxonomy")
    capabilities: list[ToolCapability] = Field(description="Supported capabilities")
    description: str = Field(description="Human & agent friendly description")
    risk_level: ToolRiskLevel = Field(description="Risk assessment classification")
    status: ToolStatus = Field(description="Current lifecycle status")
    input_schema: ToolInputSchema = Field(description="Input arguments schema")
    output_schema: ToolOutputSchema = Field(description="Output result schema")


class Tool(BaseModel):
    """Core domain model representing a registered tool definition."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        default_factory=lambda: f"tool_{uuid4().hex[:12]}", description="Unique tool identifier"
    )
    name: str = Field(description="Unique machine-readable tool name (e.g. 'filesystem.read')")
    version: str = Field(default="1.0.0", description="Semantic version string")
    description: str = Field(description="Clear description of the tool's purpose and usage")
    category: ToolCategory = Field(default=ToolCategory.UTILITY, description="Category classification")
    capabilities: list[ToolCapability] = Field(
        default_factory=lambda: [ToolCapability.TEXT_TRANSFORMATION], description="Claimed capabilities"
    )
    status: ToolStatus = Field(default=ToolStatus.REGISTERED, description="Lifecycle status")
    risk_level: ToolRiskLevel = Field(default=ToolRiskLevel.LOW, description="Risk level metadata")
    source: ToolSource = Field(default=ToolSource.BUILT_IN, description="Tool origin source")

    input_schema: ToolInputSchema = Field(default_factory=ToolInputSchema, description="Input arguments schema")
    output_schema: ToolOutputSchema = Field(default_factory=ToolOutputSchema, description="Output result schema")

    configuration: ToolConfiguration = Field(default_factory=ToolConfiguration, description="Operational configuration")
    availability: ToolAvailability = Field(default_factory=ToolAvailability, description="Availability state")

    owner_id: str = Field(default="system", description="Owner user or system identifier")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary safe metadata")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Registration timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    @model_validator(mode="after")
    def validate_tool_definition(self) -> "Tool":
        """Validate tool naming conventions and non-empty description."""
        if not self.name or not self.name.strip():
            raise InvalidToolDefinitionError("Tool name cannot be empty.")
        if " " in self.name:
            raise InvalidToolDefinitionError(f"Tool name '{self.name}' must not contain spaces.")
        if not self.description or not self.description.strip():
            raise InvalidToolDefinitionError(f"Tool '{self.name}' must have a non-empty description.")
        return self

    def to_descriptor(self) -> ToolDescriptor:
        """Export compact descriptor for AI Agent context."""
        return ToolDescriptor(
            id=self.id,
            name=self.name,
            version=self.version,
            category=self.category,
            capabilities=self.capabilities,
            description=self.description,
            risk_level=self.risk_level,
            status=self.status,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
        )


class ResolvedTool(BaseModel):
    """Resolved tool entity containing validated tool pointer and active status."""

    model_config = ConfigDict(frozen=True)

    tool_id: str = Field(description="Resolved tool ID")
    name: str = Field(description="Tool name")
    version: str = Field(description="Resolved version")
    tool: Tool = Field(description="Full tool entity")
    is_active: bool = Field(description="Whether tool is active for invocation")
    resolved_at: datetime = Field(default_factory=datetime.utcnow, description="Resolution timestamp")
