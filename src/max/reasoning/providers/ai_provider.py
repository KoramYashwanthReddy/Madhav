"""AI-backed reasoning provider adapter integrating with Module 04 AI Runtime."""

import json
import logging
from typing import Any

from max.ai.domain.enums import AIRole
from max.ai.domain.messages import AIMessage
from max.ai.domain.requests import AIRequest
from max.ai.runtime.manager import AIRuntimeManager
from max.context.domain.package import ContextPackage
from max.reasoning.domain.enums import (
    ConfidenceLevel,
    PlanStatus,
    ReasoningStatus,
)
from max.reasoning.domain.exceptions import MalformedReasoningOutputError
from max.reasoning.domain.plan import Plan, PlanRisk, PlanStep
from max.reasoning.domain.reasoning import (
    MissingInformation,
    ReasoningAssumption,
    ReasoningConclusion,
    ReasoningEvidence,
    ReasoningObservation,
    ReasoningRequest,
    ReasoningResult,
)
from max.reasoning.providers.base import ReasoningProvider

logger = logging.getLogger(__name__)


class AIReasoningProvider(ReasoningProvider):
    """ReasoningProvider implementation powered by Module 04 AI Runtime Manager."""

    def __init__(
        self,
        ai_runtime_manager: AIRuntimeManager | None = None,
        model_reference: str = "development-stub",
    ) -> None:
        self.ai_runtime_manager = ai_runtime_manager or AIRuntimeManager()
        self.model_reference = model_reference

    async def reason(
        self, request: ReasoningRequest, context_package: ContextPackage | None = None
    ) -> ReasoningResult:
        """Execute AI-backed reasoning request with structured output parsing."""
        prompt = self._build_reasoning_prompt(request, context_package)

        system_msg = AIMessage(
            role=AIRole.SYSTEM,
            content=(
                "You are an expert AI Reasoning Engine. Analyze objective and context carefully. "
                "Respond ONLY with a valid JSON object matching the requested schema. "
                "Do NOT execute any code, shell commands, or external actions."
            ),
        )
        user_msg = AIMessage(role=AIRole.USER, content=prompt)

        ai_req = AIRequest(
            messages=[system_msg, user_msg],
            model=self.model_reference,
        )

        try:
            ai_resp = await self.ai_runtime_manager.generate(ai_req)
            data = self._parse_json_response(ai_resp.content)

            # Build ReasoningResult from structured data
            observations = [
                ReasoningObservation(
                    description=obs.get("description", "Observation"),
                    source_type=obs.get("source_type", "context"),
                    source_id=obs.get("source_id", "ref"),
                )
                for obs in data.get("observations", [])
            ]

            assumptions = [
                ReasoningAssumption(
                    description=asm.get("description", "Assumption"),
                    confidence=ConfidenceLevel(asm.get("confidence", "MEDIUM")),
                    source=asm.get("source"),
                )
                for asm in data.get("assumptions", [])
            ]

            missing_info = [
                MissingInformation(
                    description=msg.get("description", "Missing information"),
                    importance=ConfidenceLevel(msg.get("importance", "MEDIUM")),
                    is_blocking=msg.get("is_blocking", False),
                )
                for msg in data.get("missing_information", [])
            ]

            conclusion_dict = data.get("conclusions", {})
            summary_txt = conclusion_dict.get(
                "summary", f"Analysis for '{request.objective.title}'."
            )
            conclusions = ReasoningConclusion(
                summary=summary_txt,
                key_findings=conclusion_dict.get("key_findings", []),
                recommendations=conclusion_dict.get("recommendations", []),
                confidence=ConfidenceLevel(conclusion_dict.get("confidence", "MEDIUM")),
            )

            evidence = [
                ReasoningEvidence(
                    source_type=ev.get("source_type", "context"),
                    source_id=ev.get("source_id", "ref"),
                    summary=ev.get("summary", "Evidence summary"),
                    location=ev.get("location"),
                )
                for ev in data.get("evidence", [])
            ]

            plan_dict = data.get("plan")
            risks_dict = data.get("risks", [])
            fallback_exp = f"Reasoning analysis for '{request.objective.title}'."
            exp_txt = data.get("explanation", fallback_exp)

            return ReasoningResult(
                request_id=request.id,
                status=ReasoningStatus.COMPLETED,
                objective_summary=request.objective.title,
                observations=observations,
                assumptions=assumptions,
                constraints=request.constraints,
                missing_information=missing_info,
                conclusions=conclusions,
                plan=plan_dict,
                risks=risks_dict,
                evidence=evidence,
                confidence=ConfidenceLevel(data.get("confidence", "MEDIUM")),
                explanation=exp_txt,
                metadata={"provider": "ai_runtime", "model": self.model_reference},
            )

        except Exception as exc:
            logger.error("AI reasoning provider execution failed: %s", exc)
            if isinstance(exc, MalformedReasoningOutputError):
                raise
            raise MalformedReasoningOutputError(
                f"Failed to process AI reasoning output: {exc}",
                details={"error": str(exc)},
            ) from exc

    async def generate_plan(
        self, request: ReasoningRequest, context_package: ContextPackage | None = None
    ) -> Plan:
        """Generate AI-backed structured Plan domain model."""
        res = await self.reason(request, context_package)
        if not res.plan:
            # Fallback construction if AI response omitted explicit plan dict
            step1 = PlanStep(
                sequence=1,
                title=f"Initial phase for {request.objective.title}",
                description="Begin initial objective planning phase.",
            )
            return Plan(
                owner_id=request.owner_id,
                title=f"Plan: {request.objective.title}",
                description=request.objective.description or request.objective.title,
                status=PlanStatus.ACTIVE,
                steps=[step1],
            )

        # Parse steps from plan dict
        raw_steps = res.plan.get("steps", [])
        steps: list[PlanStep] = []
        for idx, s in enumerate(raw_steps, start=1):
            steps.append(
                PlanStep(
                    step_id=s.get("step_id", f"step_{idx}"),
                    sequence=s.get("sequence", idx),
                    title=s.get("title", f"Step {idx}"),
                    description=s.get("description", "Step description"),
                    dependencies=s.get("dependencies", []),
                    prerequisites=s.get("prerequisites", []),
                )
            )

        if not steps:
            steps.append(
                PlanStep(
                    sequence=1,
                    title=f"Execute {request.objective.title}",
                    description="Primary execution phase.",
                )
            )

        raw_risks = res.plan.get("risks", res.risks)
        risks = [
            PlanRisk(
                description=r.get("description", "Risk item"),
                mitigation=r.get("mitigation"),
            )
            for r in raw_risks
            if isinstance(r, dict)
        ]

        return Plan(
            owner_id=request.owner_id,
            title=str(res.plan.get("title", f"Plan: {request.objective.title}")),
            description=str(res.plan.get("description", request.objective.description or "")),
            status=PlanStatus.ACTIVE,
            steps=steps,
            risks=risks,
            constraints=request.constraints,
            metadata={"provider": "ai_runtime", "model": self.model_reference},
        )

    def capabilities(self) -> dict[str, Any]:
        """Return provider capabilities."""
        return {
            "provider": "ai_runtime",
            "model_reference": self.model_reference,
            "is_production": True,
            "supports_planning": True,
        }

    def _build_reasoning_prompt(
        self, request: ReasoningRequest, context_package: ContextPackage | None
    ) -> str:
        """Construct prompt string for Module 04 AI Request."""
        lines = [
            f"Objective Title: {request.objective.title}",
            f"Objective Description: {request.objective.description}",
            f"Desired Outcome: {request.objective.desired_outcome}",
            f"Reasoning Mode: {request.mode}",
        ]
        if request.constraints:
            lines.append("Constraints:")
            for c in request.constraints:
                lines.append(f"- [{c.classification}] {c.type}: {c.description}")

        if context_package:
            lines.append("Context Package Items:")
            for item in context_package.items:
                lines.append(f"- [{item.category.value}] {item.content[:150]}")

        lines.append(
            "\nProduce a JSON response with keys: observations, assumptions, "
            "missing_information, conclusions, plan, risks, confidence, explanation."
        )

        return "\n".join(lines)

    @staticmethod
    def _parse_json_response(content: str) -> dict[str, Any]:
        """Extract and parse JSON object from text response."""
        content_clean = content.strip()
        if content_clean.startswith("```json"):
            content_clean = content_clean.removeprefix("```json")
            if content_clean.endswith("```"):
                content_clean = content_clean.removesuffix("```")
            content_clean = content_clean.strip()

        try:
            parsed = json.loads(content_clean)
            if isinstance(parsed, dict):
                return parsed
            raise MalformedReasoningOutputError("AI response is not a valid JSON object.")
        except json.JSONDecodeError as exc:
            raise MalformedReasoningOutputError(
                f"Failed to parse JSON response: {exc}",
                details={"raw_content": content[:200]},
            ) from exc
