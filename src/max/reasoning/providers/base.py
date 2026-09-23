"""Abstract Reasoning Provider interface for Module 11."""

from abc import ABC, abstractmethod
from typing import Any

from max.context.domain.package import ContextPackage
from max.reasoning.domain.plan import Plan
from max.reasoning.domain.reasoning import ReasoningRequest, ReasoningResult


class ReasoningProvider(ABC):
    """Abstract contract for cognitive reasoning and plan generation providers."""

    @abstractmethod
    async def reason(
        self, request: ReasoningRequest, context_package: ContextPackage | None = None
    ) -> ReasoningResult:
        """Perform cognitive reasoning analysis on request and return structured result."""

    @abstractmethod
    async def generate_plan(
        self, request: ReasoningRequest, context_package: ContextPackage | None = None
    ) -> Plan:
        """Generate a structured Plan domain model based on objective and context."""

    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Return diagnostic provider capabilities metadata."""
