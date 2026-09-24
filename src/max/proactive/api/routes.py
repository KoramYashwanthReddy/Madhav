"""FastAPI REST router for Module 30 — Proactive Intelligence Engine."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from max.proactive.container import ProactiveContainer
from max.proactive.domain.enums import ActionStatus, AutonomyLevel, RuleStatus
from max.proactive.domain.models import (
    ProactiveCandidate,
    ProactiveDecision,
    ProactiveFeedback,
    ProactiveRule,
    ProactiveSignal,
    ProactiveSimulationResult,
)
from max.proactive.schemas.proactive_schemas import (
    CandidateResponse,
    DecisionResponse,
    FeedbackCreateRequest,
    RuleCreateRequest,
    SignalIngestRequest,
    SignalResponse,
    StatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proactive", tags=["proactive"])


def _container() -> ProactiveContainer:
    return ProactiveContainer.get_instance()


@APIRouter.get(router, "/status", response_model=StatusResponse)
async def get_proactive_status(owner_id: str = "default_owner") -> StatusResponse:
    """Retrieve current operational status, active user state, and attention budget counts."""
    cnt = _container()
    user_state = cnt.user_profile_adapter.get_user_state(owner_id)
    budget = cnt.budget_service.get_budget(owner_id)
    rules = await cnt.rule_repo.list_rules(owner_id)
    active_count = len([r for r in rules if r.status == RuleStatus.ACTIVE])

    return StatusResponse(
        enabled=cnt.settings.enabled,
        mode=cnt.user_profile_adapter.get_proactive_mode(owner_id),
        user_state=user_state,
        default_autonomy_level=AutonomyLevel(cnt.settings.default_autonomy_level),
        hourly_notifications_remaining=max(0, budget.max_per_hour - budget.hourly_count),
        daily_notifications_remaining=max(0, budget.max_per_day - budget.daily_count),
        active_rules_count=active_count,
    )


@APIRouter.post(router, "/signals", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
async def ingest_signal(
    payload: SignalIngestRequest, owner_id: str = "default_owner"
) -> SignalResponse:
    """Ingest a new external or internal signal into the proactive intelligence pipeline."""
    cnt = _container()
    sig = ProactiveSignal(
        source=payload.source,
        signal_type=payload.signal_type,
        payload_reference=payload.payload_reference,
        importance_hint=payload.importance_hint,
        deduplication_key=payload.deduplication_key,
        owner_id=owner_id,
        metadata=payload.metadata,
    )
    results = await cnt.decision_engine.process_signal(sig)
    return SignalResponse(signal=sig, candidates_count=len(results))


@APIRouter.get(router, "/signals", response_model=list[ProactiveSignal])
async def list_signals(
    owner_id: str = "default_owner", limit: int = Query(default=50, ge=1, le=500)
) -> list[ProactiveSignal]:
    """List ingested signals for the current owner."""
    cnt = _container()
    return await cnt.signal_repo.list_signals(owner_id=owner_id, limit=limit)


@APIRouter.get(router, "/candidates", response_model=CandidateResponse)
async def list_candidates(
    owner_id: str = "default_owner", limit: int = Query(default=50, ge=1, le=500)
) -> CandidateResponse:
    """List generated proactive candidates."""
    cnt = _container()
    cands = await cnt.candidate_repo.list_candidates(owner_id=owner_id, limit=limit)
    return CandidateResponse(candidates=cands, total=len(cands))


@APIRouter.get(router, "/candidates/{candidate_id}", response_model=ProactiveCandidate)
async def get_candidate(candidate_id: str, owner_id: str = "default_owner") -> ProactiveCandidate:
    """Retrieve details of a specific candidate."""
    cnt = _container()
    cand = await cnt.candidate_repo.get_candidate(candidate_id=candidate_id, owner_id=owner_id)
    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found",
        )
    return cand


@APIRouter.post(router, "/candidates/{candidate_id}/evaluate", response_model=ProactiveDecision)
async def evaluate_candidate(
    candidate_id: str, owner_id: str = "default_owner"
) -> ProactiveDecision:
    """Force policy re-evaluation of a pending proactive candidate."""
    cnt = _container()
    cand = await cnt.candidate_repo.get_candidate(candidate_id=candidate_id, owner_id=owner_id)
    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found",
        )
    return await cnt.policy_engine.evaluate_candidate(cand, owner_id=owner_id)


@APIRouter.post(router, "/candidates/{candidate_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_candidate(
    candidate_id: str, owner_id: str = "default_owner"
) -> dict[str, Any]:
    """Dismiss a pending proactive candidate."""
    cnt = _container()
    cand = await cnt.candidate_repo.get_candidate(candidate_id=candidate_id, owner_id=owner_id)
    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found",
        )
    await cnt.audit_repo.record_event(
        owner_id=owner_id,
        event_type="CANDIDATE_DISMISSED",
        details={"candidate_id": candidate_id},
    )
    return {"status": "DISMISSED", "candidate_id": candidate_id}


@APIRouter.get(router, "/decisions", response_model=DecisionResponse)
async def list_decisions(
    owner_id: str = "default_owner", limit: int = Query(default=50, ge=1, le=500)
) -> DecisionResponse:
    """List proactive decisions made by MAX."""
    cnt = _container()
    decs = await cnt.decision_repo.list_decisions(owner_id=owner_id, limit=limit)
    return DecisionResponse(decisions=decs, total=len(decs))


@APIRouter.get(router, "/decisions/{decision_id}", response_model=ProactiveDecision)
async def get_decision(decision_id: str, owner_id: str = "default_owner") -> ProactiveDecision:
    """Retrieve details of a specific decision."""
    cnt = _container()
    dec = await cnt.decision_repo.get_decision(decision_id=decision_id, owner_id=owner_id)
    if not dec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found",
        )
    return dec


@APIRouter.post(router, "/decisions/{decision_id}/approve", status_code=status.HTTP_200_OK)
async def approve_decision_action(
    decision_id: str, owner_id: str = "default_owner"
) -> dict[str, Any]:
    """Approve a pending proactive decision action."""
    cnt = _container()
    dec = await cnt.decision_repo.get_decision(decision_id=decision_id, owner_id=owner_id)
    if not dec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found",
        )
    actions = await cnt.action_repo.list_actions(owner_id=owner_id)
    matching = [a for a in actions if a.decision_id == decision_id]
    if matching:
        matching[0].status = ActionStatus.APPROVED
        await cnt.action_repo.save_action(matching[0])
    return {"status": "APPROVED", "decision_id": decision_id}


@APIRouter.post(router, "/decisions/{decision_id}/reject", status_code=status.HTTP_200_OK)
async def reject_decision_action(
    decision_id: str, owner_id: str = "default_owner"
) -> dict[str, Any]:
    """Reject a pending proactive decision action."""
    cnt = _container()
    dec = await cnt.decision_repo.get_decision(decision_id=decision_id, owner_id=owner_id)
    if not dec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found",
        )
    actions = await cnt.action_repo.list_actions(owner_id=owner_id)
    matching = [a for a in actions if a.decision_id == decision_id]
    if matching:
        matching[0].status = ActionStatus.REJECTED
        await cnt.action_repo.save_action(matching[0])
    return {"status": "REJECTED", "decision_id": decision_id}


@APIRouter.post(router, "/feedback", response_model=ProactiveFeedback, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreateRequest, owner_id: str = "default_owner"
) -> ProactiveFeedback:
    """Submit explicit user feedback regarding a proactive decision."""
    cnt = _container()
    fb = ProactiveFeedback(
        decision_id=payload.decision_id,
        owner_id=owner_id,
        feedback_type=payload.feedback_type,
        value=payload.value,
        source=payload.source,
        metadata=payload.metadata,
    )
    return await cnt.feedback_service.record_feedback(fb)


@APIRouter.get(router, "/rules", response_model=list[ProactiveRule])
async def list_rules(
    owner_id: str = "default_owner", limit: int = Query(default=50, ge=1, le=500)
) -> list[ProactiveRule]:
    """List proactive evaluation rules."""
    cnt = _container()
    return await cnt.rule_repo.list_rules(owner_id=owner_id, limit=limit)


@APIRouter.post(router, "/rules", response_model=ProactiveRule, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: RuleCreateRequest, owner_id: str = "default_owner"
) -> ProactiveRule:
    """Create a new structured proactive rule."""
    cnt = _container()
    rule = ProactiveRule(
        owner_id=owner_id,
        name=payload.name,
        description=payload.description,
        source=payload.source,
        candidate_type=payload.candidate_type,
        min_importance=payload.min_importance,
        min_urgency=payload.min_urgency,
        min_confidence=payload.min_confidence,
        min_relevance=payload.min_relevance,
        allowed_user_states=payload.allowed_user_states,
        decision_type=payload.decision_type,
        priority=payload.priority,
        cooldown_seconds=payload.cooldown_seconds,
        metadata=payload.metadata,
    )
    return await cnt.rule_repo.save_rule(rule)


@APIRouter.get(router, "/rules/{rule_id}", response_model=ProactiveRule)
async def get_rule(rule_id: str, owner_id: str = "default_owner") -> ProactiveRule:
    """Retrieve details of a specific proactive rule."""
    cnt = _container()
    rule = await cnt.rule_repo.get_rule(rule_id=rule_id, owner_id=owner_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
    return rule


@APIRouter.put(router, "/rules/{rule_id}", response_model=ProactiveRule)
async def update_rule(
    rule_id: str, payload: RuleCreateRequest, owner_id: str = "default_owner"
) -> ProactiveRule:
    """Update an existing proactive rule."""
    cnt = _container()
    rule = await cnt.rule_repo.get_rule(rule_id=rule_id, owner_id=owner_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
    rule.name = payload.name
    rule.description = payload.description
    rule.source = payload.source
    rule.candidate_type = payload.candidate_type
    rule.min_importance = payload.min_importance
    rule.min_urgency = payload.min_urgency
    rule.min_confidence = payload.min_confidence
    rule.min_relevance = payload.min_relevance
    rule.allowed_user_states = payload.allowed_user_states
    rule.decision_type = payload.decision_type
    rule.priority = payload.priority
    rule.cooldown_seconds = payload.cooldown_seconds
    rule.metadata = payload.metadata
    return await cnt.rule_repo.save_rule(rule)


@APIRouter.post(router, "/rules/{rule_id}/enable", response_model=ProactiveRule)
async def enable_rule(rule_id: str, owner_id: str = "default_owner") -> ProactiveRule:
    """Enable a disabled proactive rule."""
    cnt = _container()
    rule = await cnt.rule_repo.get_rule(rule_id=rule_id, owner_id=owner_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
    rule.status = RuleStatus.ACTIVE
    return await cnt.rule_repo.save_rule(rule)


@APIRouter.post(router, "/rules/{rule_id}/disable", response_model=ProactiveRule)
async def disable_rule(rule_id: str, owner_id: str = "default_owner") -> ProactiveRule:
    """Disable an active proactive rule."""
    cnt = _container()
    rule = await cnt.rule_repo.get_rule(rule_id=rule_id, owner_id=owner_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
    rule.status = RuleStatus.DISABLED
    return await cnt.rule_repo.save_rule(rule)


@APIRouter.post(router, "/simulate", response_model=ProactiveSimulationResult)
async def simulate_signal(
    payload: SignalIngestRequest, owner_id: str = "default_owner"
) -> ProactiveSimulationResult:
    """Simulate proactive pipeline evaluation deterministically without side effects."""
    cnt = _container()
    sig = ProactiveSignal(
        source=payload.source,
        signal_type=payload.signal_type,
        payload_reference=payload.payload_reference,
        importance_hint=payload.importance_hint,
        deduplication_key=payload.deduplication_key,
        owner_id=owner_id,
        metadata=payload.metadata,
    )
    return await cnt.decision_engine.simulate_signal(sig)
