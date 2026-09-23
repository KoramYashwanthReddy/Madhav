"""Unit tests for Context Management services, selector, truncator, and manager."""

import pytest

from madhav.context.domain.budget import ContextBudget
from madhav.context.domain.enums import ContextCategory, ContextPriority, TruncationStrategy
from madhav.context.domain.item import ContextItem
from madhav.context.domain.policy import ContextPolicy
from madhav.context.domain.request import ContextRequest
from madhav.context.exceptions import RequiredContextOverflowError
from madhav.context.services.estimator import ApproximateTokenEstimator
from madhav.context.services.identity_adapter import IdentityProjection
from madhav.context.services.manager import ContextManager
from madhav.context.services.selector import ContextSelector
from madhav.context.services.truncator import ContextTruncator
from madhav.identity.domain.assistant import AssistantIdentity
from madhav.identity.domain.context import IdentityContext
from madhav.identity.domain.owner import OwnerIdentity
from madhav.identity.domain.profile import PersonalProfile


def test_approximate_token_estimator() -> None:
    """Test offline token estimation heuristics."""
    estimator = ApproximateTokenEstimator()
    assert estimator.estimate("") == 0
    assert estimator.estimate("Hello world") > 0
    assert estimator.estimate("This is a longer test paragraph for token estimation.") > 5


def test_identity_projection_privacy_filtering() -> None:
    """Verify safe vs sensitive field projection in IdentityProjection adapter."""
    ctx = IdentityContext(
        assistant=AssistantIdentity(name="Madhav"),
        owner=OwnerIdentity(
            preferred_name="Alice",
            email="alice@example.com",
            phone="+1234567890",
            date_of_birth="1990-01-01",
        ),
        profile=PersonalProfile(),
    )

    # 1. Safe projection (default)
    safe_items = IdentityProjection.project(ctx, allow_sensitive=False)
    combined_safe_text = " ".join([item.content for item in safe_items])
    assert "Alice" in combined_safe_text
    assert "alice@example.com" not in combined_safe_text
    assert "+1234567890" not in combined_safe_text

    # 2. Sensitive projection (explicit opt-in)
    sensitive_items = IdentityProjection.project(ctx, allow_sensitive=True)
    combined_sensitive_text = " ".join([item.content for item in sensitive_items])
    assert "alice@example.com" in combined_sensitive_text
    assert "+1234567890" in combined_sensitive_text


def test_context_truncator_strategies() -> None:
    """Test text truncation under TAIL, HEAD, and HEAD_AND_TAIL strategies."""
    estimator = ApproximateTokenEstimator()
    truncator = ContextTruncator(estimator)
    long_text = "Line " + " ".join([f"word{i}" for i in range(200)])

    item = ContextItem(content=long_text)

    # Tail truncation
    truncated_tail = truncator.truncate(
        item, target_max_tokens=20, strategy=TruncationStrategy.TAIL
    )
    assert truncated_tail.token_estimate <= 20
    assert "... [TRUNCATED TAIL]" in truncated_tail.content
    assert truncated_tail.metadata["truncated"] is True

    # Head truncation
    truncated_head = truncator.truncate(
        item, target_max_tokens=20, strategy=TruncationStrategy.HEAD
    )
    assert truncated_head.token_estimate <= 20
    assert "[TRUNCATED HEAD] ..." in truncated_head.content



def test_context_selector_priority_and_deduplication() -> None:
    """Test ContextSelector priority ordering and duplicate removal."""
    estimator = ApproximateTokenEstimator()
    selector = ContextSelector(estimator)
    budget = ContextBudget(max_tokens=4096, reserved_tokens=1024, safety_margin=256)
    policy = ContextPolicy.default()

    item_low = ContextItem(
        category=ContextCategory.OTHER,
        content="Low priority item text",
        priority=ContextPriority.LOW,
    )
    item_crit = ContextItem(
        category=ContextCategory.SYSTEM,
        content="Critical system instruction",
        priority=ContextPriority.CRITICAL,
        required=True,
    )
    item_dup = ContextItem(
        category=ContextCategory.OTHER,
        content="Low priority item text",  # Duplicate content
        priority=ContextPriority.NORMAL,
    )

    included, truncated, dropped, report = selector.select(
        candidates=[item_low, item_crit, item_dup],
        budget=budget,
        policy=policy,
    )

    assert len(included) == 2  # item_crit and item_low (item_dup deduplicated)
    assert included[0].content == "Critical system instruction"  # Required & Critical first
    assert len(dropped) == 1
    assert dropped[0]["dropped_reason"] == "duplicate"


def test_context_selector_required_overflow() -> None:
    """Verify RequiredContextOverflowError when mandatory item cannot fit in budget."""
    estimator = ApproximateTokenEstimator()
    selector = ContextSelector(estimator)
    # Tiny available budget of 5 tokens
    budget = ContextBudget(max_tokens=100, reserved_tokens=80, safety_margin=15)
    policy = ContextPolicy(truncation_strategy=TruncationStrategy.NONE)

    giant_required = ContextItem(
        category=ContextCategory.REQUEST,
        content="A " * 500,  # Far exceeds 5 tokens
        priority=ContextPriority.CRITICAL,
        required=True,
    )

    with pytest.raises(RequiredContextOverflowError, match="cannot fit within"):
        selector.select(candidates=[giant_required], budget=budget, policy=policy)



@pytest.mark.asyncio
async def test_context_manager_build_and_prepare() -> None:
    """Test full ContextManager facade context package building and AIRequest preparation."""
    manager = ContextManager()
    request = ContextRequest(user_request="Hello Madhav", model_reference="development-stub")

    package = await manager.build_context(request)
    assert package.request_id == request.request_id
    assert len(package.messages) >= 2  # System message + User request message
    assert package.token_estimate > 0

    ai_request = await manager.prepare_ai_request(request)
    assert ai_request.request_id == request.request_id
    assert len(ai_request.messages) >= 2
