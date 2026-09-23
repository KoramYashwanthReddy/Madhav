"""Capability matching service for evaluating Agent capabilities against required task capabilities."""

from pydantic import BaseModel

from madhav.agents.domain.enums import AgentCapability


class CapabilityMatchResult(BaseModel):
    """Result of capability matching evaluation."""

    matched: bool
    missing_capabilities: list[AgentCapability]


class CapabilityMatcher:
    """Evaluates capability alignment between tasks/requests and agents."""

    @staticmethod
    def match_capabilities(
        required_capabilities: list[AgentCapability],
        provided_capabilities: list[AgentCapability],
    ) -> tuple[bool, list[AgentCapability]]:
        """Check if all required capabilities are present in provided capabilities.

        Returns (is_matched, missing_capabilities).
        """
        provided_set = set(provided_capabilities)
        missing = [cap for cap in required_capabilities if cap not in provided_set]
        return len(missing) == 0, missing

    @classmethod
    def match(
        cls,
        required: list[AgentCapability],
        available: list[AgentCapability],
    ) -> CapabilityMatchResult:
        """Helper returning structured CapabilityMatchResult."""
        matched, missing = cls.match_capabilities(required, available)
        return CapabilityMatchResult(matched=matched, missing_capabilities=missing)
