"""Unit tests for Context Management domain models and value objects."""

from datetime import UTC, datetime, timedelta

import pytest

from madhav.context.domain.budget import ContextBudget
from madhav.context.domain.enums import (
    ContextCategory,
    ContextPriority,
)
from madhav.context.domain.item import ContextItem
from madhav.context.domain.policy import ContextPolicy
from madhav.context.domain.request import ContextRequest


def test_context_priority_from_string() -> None:
    """Verify priority parsing from string names."""
    assert ContextPriority.from_string("CRITICAL") == ContextPriority.CRITICAL
    assert ContextPriority.from_string("high") == ContextPriority.HIGH
    assert ContextPriority.from_string("Normal") == ContextPriority.NORMAL

    with pytest.raises(ValueError, match="Unknown ContextPriority level"):
        ContextPriority.from_string("INVALID_LEVEL")


def test_context_item_validation_and_hash() -> None:
    """Test ContextItem creation, content validation, and SHA-256 content hashing."""
    item1 = ContextItem(
        category=ContextCategory.SYSTEM,
        content="System instruction text",
        priority=ContextPriority.CRITICAL,
    )
    assert item1.content == "System instruction text"
    assert item1.category == ContextCategory.SYSTEM
    assert item1.priority == ContextPriority.CRITICAL
    assert len(item1.content_hash) == 64  # SHA-256 hex length

    # Empty content validation failure
    with pytest.raises(ValueError, match="cannot be empty"):
        ContextItem(content="   ")


def test_context_item_expiration() -> None:
    """Verify context item expiration status property."""
    now = datetime.now(UTC)
    future_item = ContextItem(content="Future item", expires_at=now + timedelta(hours=1))
    assert not future_item.is_expired

    past_item = ContextItem(content="Past item", expires_at=now - timedelta(hours=1))
    assert past_item.is_expired


def test_context_budget_bounds_and_available() -> None:
    """Verify ContextBudget calculation and validation bounds."""
    budget = ContextBudget(max_tokens=4096, reserved_tokens=1024, safety_margin=256)
    assert budget.available_input_tokens == 2816  # 4096 - 1024 - 256

    with pytest.raises(ValueError, match="must be less than model max tokens"):
        ContextBudget(max_tokens=1000, reserved_tokens=800, safety_margin=300)


def test_context_policy_presets() -> None:
    """Verify declarative ContextPolicy presets."""
    default_p = ContextPolicy.default()
    assert default_p.name == "default"
    assert not default_p.allow_sensitive_identity

    minimal_p = ContextPolicy.minimal()
    assert minimal_p.name == "minimal"
    assert len(minimal_p.allowed_categories) == 2

    full_p = ContextPolicy.full()
    assert full_p.name == "full"
    assert full_p.allow_sensitive_identity


def test_context_request_validation() -> None:
    """Verify ContextRequest validation."""
    req = ContextRequest(user_request="Hello Madhav")
    assert req.user_request == "Hello Madhav"

    with pytest.raises(ValueError, match="cannot be empty"):
        ContextRequest(user_request="")
