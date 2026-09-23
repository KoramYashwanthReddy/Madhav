"""Unit tests for MemoryService facade, duplicate detection, and expiration evaluation."""

from datetime import timedelta

import pytest

from madhav.common.clock import DeterministicClock
from madhav.memory.domain.enums import MemoryImportance, MemoryType
from madhav.memory.exceptions import (
    DuplicateMemoryError,
    MemoryOwnershipError,
    MemoryValidationError,
)
from madhav.memory.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_service_creation_and_access_tracking() -> None:
    """Verify memory creation and access tracking timestamp update."""
    clock = DeterministicClock()
    service = MemoryService(clock=clock)

    mem = await service.create_memory(
        owner_id="user_1",
        type=MemoryType.FACT,
        text="Madhav is a modular personal AI system",
        importance=MemoryImportance.HIGH,
    )
    assert mem.last_accessed_at is None

    # Advance clock and retrieve
    clock.advance(minutes=10)
    fetched = await service.get_memory(mem.memory_id, owner_id="user_1", touch_access=True)

    assert fetched.last_accessed_at is not None
    assert fetched.last_accessed_at == clock.now()


@pytest.mark.asyncio
async def test_service_duplicate_detection() -> None:
    """Verify deterministic duplicate detection raises DuplicateMemoryError."""
    service = MemoryService()

    await service.create_memory(
        owner_id="user_1",
        text="User lives in San Francisco, California",
    )

    # Creating identical memory should raise DuplicateMemoryError
    with pytest.raises(DuplicateMemoryError):
        await service.create_memory(
            owner_id="user_1",
            text="User lives in San Francisco, California",
        )


@pytest.mark.asyncio
async def test_service_ownership_and_validation() -> None:
    """Verify ownership scoping and text validation errors."""
    service = MemoryService()

    mem = await service.create_memory(owner_id="user_1", text="Private user note")

    # Access by wrong owner must raise MemoryOwnershipError
    with pytest.raises(MemoryOwnershipError):
        await service.get_memory(mem.memory_id, owner_id="user_2")

    # Empty text validation failure
    with pytest.raises(MemoryValidationError):
        await service.create_memory(owner_id="user_1", text="   ")


@pytest.mark.asyncio
async def test_service_expiration_evaluation() -> None:
    """Verify memory expiration evaluation via DeterministicClock."""
    clock = DeterministicClock()
    service = MemoryService(clock=clock)

    exp_time = clock.now() + timedelta(minutes=5)
    mem = await service.create_memory(
        owner_id="user_1",
        text="Expiring temporary token note",
        expires_at=exp_time,
    )

    # Before expiration
    is_exp1 = await service.evaluate_expiration(mem.memory_id)
    assert is_exp1 is False

    # Advance clock beyond expiration
    clock.advance(minutes=10)
    is_exp2 = await service.evaluate_expiration(mem.memory_id)
    assert is_exp2 is True
