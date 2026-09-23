"""Reasoning Service orchestrating cognitive analysis, context assembly, and plan generation."""

import logging
import time
from typing import Any

from max.context.domain.policy import ContextPolicy
from max.context.domain.request import ContextRequest
from max.context.services.manager import ContextManager
from max.reasoning.domain.exceptions import ReasoningNotFoundError
from max.reasoning.domain.plan import PlanDependency, PlanRisk, PlanStep
from max.reasoning.domain.reasoning import (
    ReasoningConstraint,
    ReasoningRequest,
    ReasoningResult,
)
from max.reasoning.providers.base import ReasoningProvider
from max.reasoning.repositories.reasoning_repository import ReasoningRepository
from max.reasoning.services.plan_service import PlanService

logger = logging.getLogger(__name__)


class ReasoningService:
    """Core service managing reasoning request processing and plan creation."""

    def __init__(
        self,
        reasoning_repository: ReasoningRepository,
        reasoning_provider: ReasoningProvider,
        plan_service: PlanService | None = None,
        context_manager: ContextManager | None = None,
    ) -> None:
        self.repository = reasoning_repository
        self.provider = reasoning_provider
        self.plan_service = plan_service or PlanService()
        self.context_manager = context_manager

    async def execute_reasoning(self, request: ReasoningRequest) -> ReasoningResult:
        """Execute a structured reasoning request.

        Privacy guarantee: Full reasoning context payloads or prompts are never logged.
        Only metadata (reasoning_id, owner_id, mode, status, execution_time_ms) is logged.
        """
        start_time = time.perf_counter()

        # 1. Assemble context via Module 06 ContextManager if available
        context_package = None
        if self.context_manager:
            try:
                ctx_request = ContextRequest(
                    user_request=request.objective.title,
                    model_reference="development-stub",
                    policy=ContextPolicy.default(),
                )
                context_package = await self.context_manager.build_context(ctx_request)
            except Exception as exc:
                logger.warning("ContextManager build_context skipped for reasoning: %s", exc)

        # 2. Invoke active ReasoningProvider
        result = await self.provider.reason(request, context_package)

        # 3. If plan payload present, create and validate Plan via PlanService
        if result.plan and isinstance(result.plan, dict):
            try:
                raw_steps = result.plan.get("steps", [])
                steps = [
                    PlanStep(
                        step_id=s.get("step_id", f"step_{idx}"),
                        sequence=s.get("sequence", idx),
                        title=s.get("title", f"Step {idx}"),
                        description=s.get("description", "Step description"),
                        dependencies=s.get("dependencies", []),
                        prerequisites=s.get("prerequisites", []),
                    )
                    for idx, s in enumerate(raw_steps, start=1)
                    if isinstance(s, dict)
                ]

                raw_deps = result.plan.get("dependencies", [])
                deps = [
                    PlanDependency(
                        source_step_id=d.get("source_step_id", ""),
                        target_step_id=d.get("target_step_id", ""),
                    )
                    for d in raw_deps
                    if isinstance(d, dict)
                ]

                raw_risks = result.plan.get("risks", result.risks)
                risks = [
                    PlanRisk(
                        description=r.get("description", "Risk"),
                        mitigation=r.get("mitigation"),
                    )
                    for r in raw_risks
                    if isinstance(r, dict)
                ]

                constraints = [
                    ReasoningConstraint(
                        type=c.get("type", "general"),
                        description=c.get("description", "Constraint"),
                    )
                    for c in result.plan.get("constraints", [])
                    if isinstance(c, dict)
                ]

                if steps:
                    desc_val = str(
                        result.plan.get(
                            "description",
                            request.objective.description or request.objective.title,
                        )
                    )
                    saved_plan = await self.plan_service.create_plan(
                        owner_id=request.owner_id,
                        title=str(result.plan.get("title", f"Plan: {request.objective.title}")),
                        description=desc_val,
                        steps=steps,
                        dependencies=deps,
                        risks=risks,
                        constraints=constraints,
                    )
                    result.plan["plan_id"] = saved_plan.plan_id
            except Exception as exc:
                logger.warning("Failed to save generated plan into PlanService: %s", exc)

        # 4. Save ReasoningResult in repository
        await self.repository.save(result)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Privacy-safe log statement
        logger.info(
            "Reasoning executed for owner %s: request_id=%s, mode=%s, status=%s, duration_ms=%.2f",
            request.owner_id,
            request.id,
            request.mode,
            result.status,
            elapsed_ms,
        )

        return result

    async def get_reasoning_result(self, request_id: str, owner_id: str) -> ReasoningResult:
        """Retrieve reasoning result by request_id."""
        result = await self.repository.get_by_request_id(request_id)
        if not result:
            raise ReasoningNotFoundError(f"Reasoning result '{request_id}' not found.")
        owner_meta = result.metadata.get("owner_id")
        if owner_meta and owner_meta != owner_id:
            raise ReasoningNotFoundError(f"Reasoning result '{request_id}' not found for owner.")
        return result

    async def get_reasoning_summary(self, request_id: str, owner_id: str) -> dict[str, Any]:
        """Retrieve user-facing reasoning summary."""
        res = await self.get_reasoning_result(request_id, owner_id)
        st_val = res.status.name if hasattr(res.status, "name") else str(res.status)
        conf_val = res.confidence.name if hasattr(res.confidence, "name") else str(res.confidence)
        return {
            "reasoning_id": res.request_id,
            "status": st_val,
            "explanation": res.explanation,
            "objective_summary": res.objective_summary,
            "confidence": conf_val,
        }

    async def status(self) -> dict[str, Any]:
        """Return diagnostic subsystem status."""
        return {
            "reasoning_enabled": True,
            "provider_info": self.provider.capabilities(),
        }
