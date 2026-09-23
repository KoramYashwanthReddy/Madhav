"""REST API endpoints for Module 11 Reasoning & Planning Engine."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from madhav.reasoning.domain.enums import CompletenessStatus
from madhav.reasoning.domain.exceptions import ReasoningError
from madhav.reasoning.domain.plan import (
    Plan,
    PlanDependency,
    PlanRisk,
    PlanStep,
)
from madhav.reasoning.domain.reasoning import (
    ReasoningConstraint,
    ReasoningObjective,
    ReasoningRequest,
)
from madhav.reasoning.providers.dev_provider import DevelopmentReasoningProvider
from madhav.reasoning.repositories.plan_repository import InMemoryPlanRepository
from madhav.reasoning.repositories.plan_version_repository import InMemoryPlanVersionRepository
from madhav.reasoning.repositories.reasoning_repository import InMemoryReasoningRepository
from madhav.reasoning.schemas.requests import (
    CreatePlanPayload,
    CreateReasoningRequestPayload,
    RevisePlanPayload,
)
from madhav.reasoning.schemas.responses import (
    AssumptionResponse,
    ConclusionResponse,
    ConstraintResponse,
    MissingInformationResponse,
    ObservationResponse,
    PlanDependencyResponse,
    PlanDiffResponse,
    PlanListResponse,
    PlanResponse,
    PlanRiskResponse,
    PlanStepResponse,
    PlanValidationResponse,
    PlanVersionResponse,
    ReasoningResultResponse,
    ReasoningSummaryResponse,
)
from madhav.reasoning.services.plan_service import PlanService
from madhav.reasoning.services.reasoning_service import ReasoningService

reasoning_router = APIRouter(prefix="/reasoning", tags=["Reasoning Engine"])
plan_router = APIRouter(prefix="/plans", tags=["Planning Engine"])

_reasoning_service_instance: ReasoningService | None = None
_plan_service_instance: PlanService | None = None


def get_reasoning_services() -> tuple[ReasoningService, PlanService]:
    """Dependency provider returning active reasoning service singletons."""
    global _reasoning_service_instance, _plan_service_instance
    if _reasoning_service_instance is None or _plan_service_instance is None:
        plan_repo = InMemoryPlanRepository()
        version_repo = InMemoryPlanVersionRepository()
        reasoning_repo = InMemoryReasoningRepository()
        provider = DevelopmentReasoningProvider()

        _plan_service_instance = PlanService(
            plan_repository=plan_repo,
            version_repository=version_repo,
        )
        _reasoning_service_instance = ReasoningService(
            reasoning_repository=reasoning_repo,
            reasoning_provider=provider,
            plan_service=_plan_service_instance,
        )
    return _reasoning_service_instance, _plan_service_instance


def get_reasoning_service(
    services: tuple[ReasoningService, PlanService] = Depends(get_reasoning_services),
) -> ReasoningService:
    """Dependency provider returning ReasoningService."""
    return services[0]


def get_plan_service(
    services: tuple[ReasoningService, PlanService] = Depends(get_reasoning_services),
) -> PlanService:
    """Dependency provider returning PlanService."""
    return services[1]


def set_reasoning_services(
    reasoning_service: ReasoningService | None,
    plan_service: PlanService | None,
) -> None:
    """Helper to set or reset singleton services for testing."""
    global _reasoning_service_instance, _plan_service_instance
    _reasoning_service_instance = reasoning_service
    _plan_service_instance = plan_service


def _map_plan_response(plan: Plan) -> PlanResponse:
    """Map Plan domain model to PlanResponse schema."""
    return PlanResponse(
        plan_id=plan.plan_id,
        owner_id=plan.owner_id,
        title=plan.title,
        description=plan.description,
        version=plan.version,
        status=plan.status,
        steps=[
            PlanStepResponse(
                step_id=s.step_id,
                sequence=s.sequence,
                title=s.title,
                description=s.description,
                objective=s.objective,
                prerequisites=s.prerequisites,
                dependencies=s.dependencies,
                expected_output=s.expected_output,
                estimated_complexity=s.estimated_complexity,
                risk_level=s.risk_level,
                status=s.status,
            )
            for s in plan.steps
        ],
        dependencies=[
            PlanDependencyResponse(
                source_step_id=d.source_step_id,
                target_step_id=d.target_step_id,
                dependency_type=d.dependency_type,
            )
            for d in plan.dependencies
        ],
        risks=[
            PlanRiskResponse(
                id=r.id,
                description=r.description,
                severity=r.severity,
                likelihood=r.likelihood,
                affected_step_id=r.affected_step_id,
                mitigation=r.mitigation,
            )
            for r in plan.risks
        ],
        constraints=[
            ConstraintResponse(
                id=c.id,
                type=c.type,
                description=c.description,
                priority=c.priority,
                classification=c.classification,
            )
            for c in plan.constraints
        ],
        metadata=plan.metadata,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


# --- REASONING ENDPOINTS ---

@reasoning_router.post("", response_model=ReasoningResultResponse, status_code=201)
async def create_reasoning_request(
    req: CreateReasoningRequestPayload,
    service: ReasoningService = Depends(get_reasoning_service),
) -> ReasoningResultResponse:
    """Create and execute a cognitive reasoning request."""
    try:
        constraints = [
            ReasoningConstraint(
                type=c.type,
                description=c.description,
                priority=c.priority,
                classification=c.classification,
            )
            for c in req.constraints
        ]

        obj_constraints = [
            ReasoningConstraint(
                type=c.type,
                description=c.description,
                priority=c.priority,
                classification=c.classification,
            )
            for c in req.objective.constraints
        ]

        objective = ReasoningObjective(
            title=req.objective.title,
            description=req.objective.description,
            desired_outcome=req.objective.desired_outcome,
            success_criteria=req.objective.success_criteria,
            priority=req.objective.priority,
            constraints=obj_constraints,
        )

        domain_req = ReasoningRequest(
            owner_id=req.owner_id,
            objective=objective,
            mode=req.mode,
            constraints=constraints,
            plan_depth=req.plan_depth,
            metadata=req.metadata,
        )

        result = await service.execute_reasoning(domain_req)

        return ReasoningResultResponse(
            request_id=result.request_id,
            status=result.status,
            objective_summary=result.objective_summary,
            observations=[
                ObservationResponse(
                    id=o.id,
                    description=o.description,
                    source_type=o.source_type,
                    source_id=o.source_id,
                    timestamp=o.timestamp,
                )
                for o in result.observations
            ],
            assumptions=[
                AssumptionResponse(
                    id=a.id,
                    description=a.description,
                    confidence=a.confidence,
                    source=a.source,
                    status=a.status,
                )
                for a in result.assumptions
            ],
            constraints=[
                ConstraintResponse(
                    id=c.id,
                    type=c.type,
                    description=c.description,
                    priority=c.priority,
                    classification=c.classification,
                )
                for c in result.constraints
            ],
            missing_information=[
                MissingInformationResponse(
                    id=m.id,
                    description=m.description,
                    importance=m.importance,
                    is_blocking=m.is_blocking,
                )
                for m in result.missing_information
            ],
            conclusions=ConclusionResponse(
                summary=result.conclusions.summary,
                key_findings=result.conclusions.key_findings,
                recommendations=result.conclusions.recommendations,
                confidence=result.conclusions.confidence,
            ),
            plan=result.plan,
            risks=result.risks,
            confidence=result.confidence,
            explanation=result.explanation,
            metadata=result.metadata,
            created_at=result.created_at,
        )
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@reasoning_router.get("/summary", response_model=ReasoningSummaryResponse)
async def reasoning_summary(
    service: ReasoningService = Depends(get_reasoning_service),
) -> ReasoningSummaryResponse:
    """Get reasoning subsystem diagnostic status summary."""
    st = await service.status()
    return ReasoningSummaryResponse(
        reasoning_enabled=st["reasoning_enabled"],
        provider_info=st["provider_info"],
    )


@reasoning_router.post("/{reasoning_id}/validate", response_model=PlanValidationResponse)
async def validate_reasoning_plan(
    reasoning_id: str,
    owner_id: str = Query(..., description="Owner user ID"),
    service: ReasoningService = Depends(get_reasoning_service),
) -> PlanValidationResponse:
    """Validate plan associated with a reasoning result."""
    try:
        res = await service.get_reasoning_result(reasoning_id, owner_id)
        if res.plan and "plan_id" in res.plan:
            pid = str(res.plan["plan_id"])
            val_res = await service.plan_service.validate_plan_id(pid, owner_id)
            return PlanValidationResponse(

                is_valid=val_res.is_valid,
                status=val_res.status,
                errors=val_res.errors,
                warnings=val_res.warnings,
                has_circular_dependencies=val_res.has_circular_dependencies,
            )
        return PlanValidationResponse(
            is_valid=True,
            status=CompletenessStatus.PARTIAL,
            errors=[],
            warnings=[],
            has_circular_dependencies=False,
        )
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc



@reasoning_router.get("/{reasoning_id}/summary")
async def get_reasoning_result_summary(
    reasoning_id: str,
    owner_id: str = Query(..., description="Owner user ID"),
    service: ReasoningService = Depends(get_reasoning_service),
) -> dict[str, Any]:
    """Get concise user-facing reasoning summary."""
    try:
        return await service.get_reasoning_summary(reasoning_id, owner_id)
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@reasoning_router.get("/{reasoning_id}", response_model=ReasoningResultResponse)
async def get_reasoning_result(
    reasoning_id: str,
    owner_id: str = Query(..., description="Owner user ID"),
    service: ReasoningService = Depends(get_reasoning_service),
) -> ReasoningResultResponse:

    """Get stored reasoning result by request_id."""
    res = await service.get_reasoning_result(reasoning_id, owner_id)
    if not res:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Reasoning result '{reasoning_id}' not found.",
                "code": "REASONING_NOT_FOUND",
            },
        )

    return ReasoningResultResponse(
        request_id=res.request_id,
        status=res.status,
        objective_summary=res.objective_summary,
        observations=[
            ObservationResponse(
                id=o.id,
                description=o.description,
                source_type=o.source_type,
                source_id=o.source_id,
                timestamp=o.timestamp,
            )
            for o in res.observations
        ],
        assumptions=[
            AssumptionResponse(
                id=a.id,
                description=a.description,
                confidence=a.confidence,
                source=a.source,
                status=a.status,
            )
            for a in res.assumptions
        ],
        constraints=[
            ConstraintResponse(
                id=c.id,
                type=c.type,
                description=c.description,
                priority=c.priority,
                classification=c.classification,
            )
            for c in res.constraints
        ],
        missing_information=[
            MissingInformationResponse(
                id=m.id,
                description=m.description,
                importance=m.importance,
                is_blocking=m.is_blocking,
            )
            for m in res.missing_information
        ],
        conclusions=ConclusionResponse(
            summary=res.conclusions.summary,
            key_findings=res.conclusions.key_findings,
            recommendations=res.conclusions.recommendations,
            confidence=res.conclusions.confidence,
        ),
        plan=res.plan,
        risks=res.risks,
        confidence=res.confidence,
        explanation=res.explanation,
        metadata=res.metadata,
        created_at=res.created_at,
    )


# --- PLAN ENDPOINTS ---

@plan_router.post("", response_model=PlanResponse, status_code=201)
async def create_plan(
    req: CreatePlanPayload,
    service: PlanService = Depends(get_plan_service),
) -> PlanResponse:
    """Create a new plan directly."""
    try:
        steps = [
            PlanStep(
                step_id=s.step_id or f"step_{idx}",
                sequence=s.sequence,
                title=s.title,
                description=s.description,
                dependencies=s.dependencies,
                prerequisites=s.prerequisites,
                estimated_complexity=s.estimated_complexity,
                risk_level=s.risk_level,
                status=s.status,
            )
            for idx, s in enumerate(req.steps, start=1)
        ]

        deps = [
            PlanDependency(
                source_step_id=d.source_step_id,
                target_step_id=d.target_step_id,
            )
            for d in req.dependencies
        ]

        risks = [
            PlanRisk(
                description=r.description,
                severity=r.severity,
                likelihood=r.likelihood,
                mitigation=r.mitigation,
            )
            for r in req.risks
        ]

        constraints = [
            ReasoningConstraint(
                type=c.type,
                description=c.description,
                priority=c.priority,
                classification=c.classification,
            )
            for c in req.constraints
        ]

        plan = await service.create_plan(
            owner_id=req.owner_id,
            title=req.title,
            description=req.description,
            steps=steps,
            dependencies=deps,
            risks=risks,
            constraints=constraints,
            metadata=req.metadata,
        )
        return _map_plan_response(plan)
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@plan_router.get("", response_model=PlanListResponse)
async def list_plans(
    owner_id: str = Query(..., description="Owner user ID"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: PlanService = Depends(get_plan_service),
) -> PlanListResponse:
    """List plans owned by owner_id."""
    plans = await service.list_plans(owner_id, skip=skip, limit=limit)
    total = await service.plan_repository.count_plans(owner_id)
    return PlanListResponse(
        plans=[_map_plan_response(p) for p in plans],
        total=total,
        skip=skip,
        limit=limit,
    )


@plan_router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: str,
    owner_id: str = Query(..., description="Owner user ID"),
    service: PlanService = Depends(get_plan_service),
) -> PlanResponse:
    """Get plan details by ID."""
    try:
        plan = await service.get_plan(plan_id, owner_id)
        return _map_plan_response(plan)
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@plan_router.post("/{plan_id}/validate", response_model=PlanValidationResponse)
async def validate_plan(
    plan_id: str,
    owner_id: str = Query(..., description="Owner user ID"),
    service: PlanService = Depends(get_plan_service),
) -> PlanValidationResponse:
    """Validate stored plan structural integrity and dependencies."""
    try:
        res = await service.validate_plan_id(plan_id, owner_id)
        return PlanValidationResponse(
            is_valid=res.is_valid,
            status=res.status,
            errors=res.errors,
            warnings=res.warnings,
            has_circular_dependencies=res.has_circular_dependencies,
        )
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@plan_router.post("/{plan_id}/revise", response_model=PlanResponse)
async def revise_plan(
    plan_id: str,
    req: RevisePlanPayload,
    owner_id: str = Query(..., description="Owner user ID"),
    service: PlanService = Depends(get_plan_service),
) -> PlanResponse:
    """Revise an existing plan, creating a new PlanVersion snapshot."""
    try:
        new_steps = (
            [
                PlanStep(
                    step_id=s.step_id or f"step_{idx}",
                    sequence=s.sequence,
                    title=s.title,
                    description=s.description,
                    dependencies=s.dependencies,
                    prerequisites=s.prerequisites,
                    estimated_complexity=s.estimated_complexity,
                    risk_level=s.risk_level,
                    status=s.status,
                )
                for idx, s in enumerate(req.steps, start=1)
            ]
            if req.steps is not None
            else None
        )

        new_deps = (
            [
                PlanDependency(
                    source_step_id=d.source_step_id,
                    target_step_id=d.target_step_id,
                )
                for d in req.dependencies
            ]
            if req.dependencies is not None
            else None
        )

        new_risks = (
            [
                PlanRisk(
                    description=r.description,
                    severity=r.severity,
                    likelihood=r.likelihood,
                    mitigation=r.mitigation,
                )
                for r in req.risks
            ]
            if req.risks is not None
            else None
        )

        new_constraints = (
            [
                ReasoningConstraint(
                    type=c.type,
                    description=c.description,
                    priority=c.priority,
                    classification=c.classification,
                )
                for c in req.constraints
            ]
            if req.constraints is not None
            else None
        )

        revised = await service.revise_plan(
            plan_id=plan_id,
            owner_id=owner_id,
            reason_for_change=req.reason_for_change,
            new_steps=new_steps,
            new_dependencies=new_deps,
            new_risks=new_risks,
            new_constraints=new_constraints,
        )
        return _map_plan_response(revised)
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@plan_router.get("/{plan_id}/versions", response_model=list[PlanVersionResponse])
async def list_plan_versions(
    plan_id: str,
    owner_id: str = Query(..., description="Owner user ID"),
    service: PlanService = Depends(get_plan_service),
) -> list[PlanVersionResponse]:
    """List historical version snapshots for a plan."""
    try:
        versions = await service.get_plan_versions(plan_id, owner_id)
        return [
            PlanVersionResponse(
                version_id=v.version_id,
                plan_id=v.plan_id,
                version_number=v.version_number,
                created_at=v.created_at,
                reason_for_change=v.reason_for_change,
                previous_version_id=v.previous_version_id,
                snapshot=v.snapshot,
            )
            for v in versions
        ]
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@plan_router.post("/{plan_id}/compare/{v1}/{v2}", response_model=PlanDiffResponse)
async def compare_plan_versions(
    plan_id: str,
    v1: int,
    v2: int,
    owner_id: str = Query(..., description="Owner user ID"),
    service: PlanService = Depends(get_plan_service),
) -> PlanDiffResponse:
    """Compare two version snapshots of a plan."""
    try:
        diff = await service.compare_plan_versions(plan_id, owner_id, v1, v2)
        return PlanDiffResponse(
            added_steps=diff.added_steps,
            removed_steps=diff.removed_steps,
            changed_steps=diff.changed_steps,
            changed_dependencies=diff.changed_dependencies,
            changed_constraints=diff.changed_constraints,
            changed_risks=diff.changed_risks,
        )
    except ReasoningError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc
