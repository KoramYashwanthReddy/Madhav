"""API response DTO models for Context Management endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.context.domain.report import ContextSelectionReport


class ContextItemSummary(BaseModel):
    """Diagnostic summary representation of a single ContextItem."""

    context_id: str = Field(description="Context item unique identifier")
    category: str = Field(description="Category taxonomy string")
    priority: str = Field(description="Priority name string")
    token_estimate: int = Field(description="Estimated token count")
    source: str = Field(description="Context source identifier")
    required: bool = Field(description="Mandatory requirement flag")
    truncated: bool = Field(default=False, description="Truncation indicator")


class ContextPackageResponse(BaseModel):
    """API response model summarizing assembled ContextPackage details."""

    request_id: str = Field(description="Correlation request identifier")
    message_count: int = Field(description="Total converted AIMessage count")
    item_count: int = Field(description="Included ContextItem count")
    token_estimate: int = Field(description="Total estimated token count")
    available_budget: int = Field(description="Net available input token budget")
    policy_used: str = Field(description="Name of context policy enforced")
    items_summary: list[ContextItemSummary] = Field(
        default_factory=list, description="Diagnostic summary list of included items"
    )
    dropped_items: list[dict[str, Any]] = Field(
        default_factory=list, description="List of dropped item metadata records"
    )
    report: ContextSelectionReport = Field(description="Detailed selection report")
    created_at: datetime = Field(description="Package creation timestamp")
    messages: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional raw message contents (populated if debug_enabled=True)",
    )


class ContextSourceSummary(BaseModel):
    """Diagnostic metadata describing a registered ContextSource."""

    source_id: str = Field(description="Unique source identifier")
    category: str = Field(description="Default category taxonomy")
    priority: int = Field(description="Default priority numeric value")
    enabled: bool = Field(description="Active status flag")


class ContextSourcesResponse(BaseModel):
    """API response model listing registered ContextSources."""

    sources: list[ContextSourceSummary] = Field(description="List of registered context sources")
    total: int = Field(description="Total registered sources count")


class ContextPolicySummary(BaseModel):
    """Diagnostic metadata describing a ContextPolicy preset."""

    name: str = Field(description="Policy preset name")
    allowed_categories: list[str] = Field(description="List of permitted categories")
    required_categories: list[str] = Field(description="List of mandatory categories")
    max_items: int = Field(description="Maximum candidate items limit")
    allow_sensitive_identity: bool = Field(description="Sensitive identity opt-in flag")


class ContextPoliciesResponse(BaseModel):
    """API response model listing available ContextPolicy presets."""

    policies: list[ContextPolicySummary] = Field(description="List of policy presets")
