"""Unit tests for deterministic PermissionEvaluator engine."""

from max.security.domain.decision import SecurityContext
from max.security.domain.enums import (
    DecisionReason,
    PermissionAction,
    PermissionDecisionStatus,
    PermissionEffect,
    PermissionSubjectType,
)
from max.security.domain.permission import PermissionCondition, PermissionPolicy, PermissionRule
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject, SecurityPrincipal
from max.security.repositories.policy_repository import InMemoryPolicyRepository
from max.security.services.evaluator import PermissionEvaluator


def test_evaluator_default_deny() -> None:
    repo = InMemoryPolicyRepository()
    evaluator = PermissionEvaluator(policy_repository=repo)

    subject = PermissionSubject(subject_type=PermissionSubjectType.AGENT, subject_id="agent_1")
    principal = SecurityPrincipal(subject=subject, owner_id="owner_1")
    resource = PermissionResource(
        resource_type="FILE", resource_id="/proj/test.py", owner_id="owner_1"
    )

    context = SecurityContext(
        principal=principal,
        owner_id="owner_1",
        action=PermissionAction.READ,
        resource=resource,
    )

    decision = evaluator.evaluate(context, request_id="req_1")
    assert decision.status == PermissionDecisionStatus.DENIED
    assert decision.reason == DecisionReason.NO_POLICY_MATCH


def test_evaluator_explicit_allow_policy() -> None:
    repo = InMemoryPolicyRepository()
    policy = PermissionPolicy(
        name="Allow Read Files",
        owner_id="owner_1",
        priority=100,
        rules=[
            PermissionRule(
                effect=PermissionEffect.ALLOW,
                action_conditions=[
                    PermissionCondition(field="action", operator="EQUALS", value="READ")
                ],
            )
        ],
    )
    repo.save(policy)
    evaluator = PermissionEvaluator(policy_repository=repo)

    subject = PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="user_1")
    principal = SecurityPrincipal(subject=subject, owner_id="owner_1")
    resource = PermissionResource(
        resource_type="FILE", resource_id="/proj/test.py", owner_id="owner_1"
    )

    context = SecurityContext(
        principal=principal,
        owner_id="owner_1",
        action=PermissionAction.READ,
        resource=resource,
    )

    decision = evaluator.evaluate(context, request_id="req_1")
    assert decision.status == PermissionDecisionStatus.ALLOWED
    assert decision.reason == DecisionReason.EXPLICIT_ALLOW


def test_evaluator_explicit_deny_overrides_allow() -> None:
    repo = InMemoryPolicyRepository()

    allow_policy = PermissionPolicy(
        name="Allow All Read",
        owner_id="owner_1",
        priority=10,
        rules=[PermissionRule(effect=PermissionEffect.ALLOW)],
    )

    deny_policy = PermissionPolicy(
        name="Deny Delete System",
        owner_id="owner_1",
        priority=200,  # Higher priority
        rules=[
            PermissionRule(
                effect=PermissionEffect.DENY,
                action_conditions=[
                    PermissionCondition(field="action", operator="EQUALS", value="DELETE")
                ],
            )
        ],
    )

    repo.save(allow_policy)
    repo.save(deny_policy)
    evaluator = PermissionEvaluator(policy_repository=repo)

    subject = PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="user_1")
    principal = SecurityPrincipal(subject=subject, owner_id="owner_1")
    resource = PermissionResource(
        resource_type="FILE", resource_id="/proj/test.py", owner_id="owner_1"
    )

    context = SecurityContext(
        principal=principal,
        owner_id="owner_1",
        action=PermissionAction.DELETE,
        resource=resource,
    )

    decision = evaluator.evaluate(context, request_id="req_1")
    assert decision.status == PermissionDecisionStatus.DENIED
    assert decision.reason == DecisionReason.EXPLICIT_DENY
