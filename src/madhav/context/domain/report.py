"""ContextSelectionReport domain model providing diagnostic explanation for context selection."""

from typing import Any

from pydantic import BaseModel, Field


class ContextSelectionReport(BaseModel):
    """Detailed diagnostic explanation report produced during context selection."""

    included_items: int = Field(
        default=0, description="Count of candidate items selected and included", ge=0
    )
    truncated_items: int = Field(
        default=0, description="Count of selected items that were truncated", ge=0
    )
    dropped_items: int = Field(
        default=0, description="Count of candidate items dropped due to policy or budget", ge=0
    )

    total_estimated_tokens: int = Field(
        default=0, description="Total estimated token count consumed by included items", ge=0
    )
    available_budget: int = Field(
        default=0, description="Net available input token budget allocated for request", ge=0
    )
    policy_used: str = Field(default="default", description="Name of context policy enforced")
    summary: dict[str, Any] = Field(
        default_factory=dict, description="Categorical breakdown of selection metrics"
    )
