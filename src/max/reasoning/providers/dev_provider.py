"""Development deterministic reasoning provider for testing and offline execution.

IMPORTANT:
This provider generates deterministic structured reasoning results and plans.
It is ONLY for unit testing, integration testing, and local development.
It DOES NOT provide real general artificial intelligence reasoning.
"""

from typing import Any

from max.context.domain.package import ContextPackage
from max.reasoning.domain.enums import (
    ComplexityLevel,
    ConfidenceLevel,
    PlanStatus,
    PlanStepStatus,
    ReasoningMode,
    ReasoningStatus,
    RiskLevel,
)
from max.reasoning.domain.plan import Plan, PlanDependency, PlanRisk, PlanStep
from max.reasoning.domain.reasoning import (
    MissingInformation,
    ReasoningAssumption,
    ReasoningConclusion,
    ReasoningConstraint,
    ReasoningEvidence,
    ReasoningObservation,
    ReasoningRequest,
    ReasoningResult,
)
from max.reasoning.providers.base import ReasoningProvider


class DevelopmentReasoningProvider(ReasoningProvider):
    """Deterministic, zero-dependency reasoning provider for local development and testing."""

    def __init__(self, provider_id: str = "dev-deterministic-v1") -> None:
        self.provider_id = provider_id

    async def reason(
        self, request: ReasoningRequest, context_package: ContextPackage | None = None
    ) -> ReasoningResult:
        """Generate a deterministic structured reasoning result."""
        # 1. Generate observations from context package or request context
        observations: list[ReasoningObservation] = []
        evidence: list[ReasoningEvidence] = []

        if context_package:
            for item in context_package.items:
                obs = ReasoningObservation(
                    description=f"Observed {item.category.value}: {item.content[:60]}...",
                    source_type=str(item.source),
                    source_id=item.context_id,
                )
                observations.append(obs)
                evidence.append(
                    ReasoningEvidence(
                        source_type=str(item.source),
                        source_id=item.context_id,
                        summary=item.content[:100],
                    )
                )

        if not observations:
            observations.append(
                ReasoningObservation(
                    description=f"Objective analyzed: '{request.objective.title}'",
                    source_type="request",
                    source_id=request.id,
                )
            )

        # 2. Extract assumptions & constraints
        assumptions = list(request.context.assumptions)
        if not assumptions:
            assumptions.append(
                ReasoningAssumption(
                    description="Environment prerequisites are satisfied.",
                    confidence=ConfidenceLevel.MEDIUM,
                    source="default_dev_assumption",
                )
            )

        constraints = list(request.constraints) + list(request.objective.constraints)
        if not constraints:
            constraints.append(
                ReasoningConstraint(
                    type="system",
                    description="Deterministic dev environment constraint",
                )
            )

        # 3. Detect missing information
        missing_info: list[MissingInformation] = []
        if "deploy" in request.objective.title.lower():
            missing_info.append(
                MissingInformation(
                    description="Target deployment infrastructure provider specified.",
                    importance=ConfidenceLevel.HIGH,
                    is_blocking=False,
                )
            )

        # 4. Generate plan if mode is PLANNING or DECOMPOSITION
        plan_domain: Plan | None = None
        plan_dict: dict[str, Any] | None = None
        risks_dict: list[dict[str, Any]] = []

        planning_modes = (
            ReasoningMode.PLANNING,
            ReasoningMode.DECOMPOSITION,
            ReasoningMode.PROBLEM_SOLVING,
        )
        if request.mode in planning_modes:
            plan_domain = await self.generate_plan(request, context_package)
            plan_dict = plan_domain.model_dump()
            risks_dict = [r.model_dump() for r in plan_domain.risks]

        # 5. Build conclusions
        obj_txt = request.objective.title
        summary_txt = (
            f"Analysis completed for objective '{obj_txt}'. Target plan structured into phases."
        )
        conclusion = ReasoningConclusion(
            summary=summary_txt,
            key_findings=[
                f"Mode evaluated: {request.mode}",
                f"Constraints identified: {len(constraints)}",
                f"Observations gathered: {len(observations)}",
            ],
            recommendations=[
                "Review plan step dependencies before proceeding.",
                "Verify environmental assumptions.",
            ],
            confidence=ConfidenceLevel.HIGH,
        )

        return ReasoningResult(
            request_id=request.id,
            status=ReasoningStatus.COMPLETED,
            objective_summary=request.objective.title,
            observations=observations,
            assumptions=assumptions,
            constraints=constraints,
            missing_information=missing_info,
            conclusions=conclusion,
            plan=plan_dict,
            risks=risks_dict,
            evidence=evidence,
            confidence=ConfidenceLevel.HIGH,
            explanation=f"Deterministic reasoning result for '{request.objective.title}'.",
            metadata={
                "provider": "development",
                "provider_id": self.provider_id,
                "is_deterministic": True,
            },
        )

    async def generate_plan(
        self, request: ReasoningRequest, context_package: ContextPackage | None = None
    ) -> Plan:
        """Generate a deterministic Plan domain model."""
        obj_title = request.objective.title

        # Step 1: Preparation
        step1 = PlanStep(
            sequence=1,
            title=f"Prepare requirements for {obj_title}",
            description="Analyze objective parameters, target scope, and prerequisites.",
            objective="Establish baseline environment",
            estimated_complexity=ComplexityLevel.LOW,
            risk_level=RiskLevel.LOW,
            status=PlanStepStatus.READY,
        )

        # Step 2: Implementation
        step2 = PlanStep(
            sequence=2,
            title=f"Implement core elements for {obj_title}",
            description="Execute core construction sequence for objective components.",
            objective="Fulfill primary goal",
            dependencies=[step1.step_id],
            estimated_complexity=ComplexityLevel.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            status=PlanStepStatus.PENDING,
        )

        # Step 3: Verification
        step3 = PlanStep(
            sequence=3,
            title=f"Validate and verify {obj_title}",
            description="Perform structural validation and verification testing.",
            objective="Ensure quality compliance",
            dependencies=[step2.step_id],
            estimated_complexity=ComplexityLevel.LOW,
            risk_level=RiskLevel.LOW,
            status=PlanStepStatus.PENDING,
        )

        steps = [step1, step2, step3]

        deps = [
            PlanDependency(source_step_id=step1.step_id, target_step_id=step2.step_id),
            PlanDependency(source_step_id=step2.step_id, target_step_id=step3.step_id),
        ]

        risks = [
            PlanRisk(
                description="Potential scope ambiguity during implementation phase.",
                severity=RiskLevel.MEDIUM,
                likelihood=RiskLevel.LOW,
                affected_step_id=step2.step_id,
                mitigation="Clarify requirements during Step 1 preparation.",
            )
        ]

        constraints = list(request.constraints) + list(request.objective.constraints)

        return Plan(
            owner_id=request.owner_id,
            title=f"Plan: {obj_title}",
            description=request.objective.description or f"Deterministic plan for {obj_title}",
            status=PlanStatus.ACTIVE,
            steps=steps,
            dependencies=deps,
            risks=risks,
            constraints=constraints,
            metadata={
                "provider": "development",
                "request_id": request.id,
            },
        )

    def capabilities(self) -> dict[str, Any]:
        """Return provider capabilities."""
        return {
            "provider": "development",
            "provider_id": self.provider_id,
            "is_production": False,
            "supports_modes": [m.value for m in ReasoningMode],
            "supports_planning": True,
        }
