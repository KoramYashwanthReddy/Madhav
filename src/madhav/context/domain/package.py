"""ContextPackage domain model representing the final assembled context output."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from madhav.ai.domain.messages import AIMessage
from madhav.context.domain.budget import ContextBudget
from madhav.context.domain.item import ContextItem
from madhav.context.domain.report import ContextSelectionReport


class ContextPackage(BaseModel):
    """Deterministic outcome package containing selected context items and converted AI messages."""

    request_id: str = Field(description="Correlation request identifier matching ContextRequest")
    messages: list[AIMessage] = Field(
        description="Ordered list of AIMessage objects ready for AI Runtime consumption"
    )
    items: list[ContextItem] = Field(
        description="List of selected ContextItem objects included in package"
    )

    token_estimate: int = Field(
        description="Total estimated tokens consumed by assembled context package", ge=0
    )
    budget: ContextBudget = Field(description="ContextBudget constraints applied during selection")
    truncated_items: list[ContextItem] = Field(
        default_factory=list, description="List of items that underwent content truncation"
    )
    dropped_items: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Metadata list of items excluded with drop reasons",
    )
    report: ContextSelectionReport = Field(
        default_factory=ContextSelectionReport,
        description="Diagnostic selection summary report",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Package assembly UTC timestamp",
    )
