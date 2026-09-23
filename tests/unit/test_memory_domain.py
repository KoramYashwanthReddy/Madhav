"""Unit tests for Module 08 Memory domain models and Clock abstraction."""

from datetime import UTC, datetime, timedelta

from max.common.clock import DeterministicClock
from max.memory.domain.content import MemoryContent
from max.memory.domain.enums import MemoryImportance, MemoryStatus, MemoryType
from max.memory.domain.memory import Memory


def test_memory_domain_defaults() -> None:
    """Verify Memory aggregate default attributes and helper methods."""
    content = MemoryContent(text="User prefers dark theme mode")
    mem = Memory(owner_id="owner_1", content=content)

    assert mem.owner_id == "owner_1"
    assert mem.type == MemoryType.FACT
    assert mem.status == MemoryStatus.ACTIVE
    assert mem.is_active() is True
    assert mem.is_archived() is False
    assert mem.is_deleted() is False
    assert mem.importance == MemoryImportance.NORMAL
    assert mem.last_accessed_at is None


def test_memory_content_hash() -> None:
    """Verify SHA-256 content hash generation for duplicate checks."""
    c1 = MemoryContent(
        text="Koram Yashwanth lives in Bengaluru", structured_data={"city": "Bengaluru"}
    )
    c2 = MemoryContent(
        text="koram  yashwanth   lives in bengaluru ", structured_data={"city": "Bengaluru"}
    )
    c3 = MemoryContent(text="Different content text")

    assert c1.content_hash == c2.content_hash
    assert c1.content_hash != c3.content_hash


def test_deterministic_clock_and_expiration() -> None:
    """Verify DeterministicClock advancement and memory expiration evaluation."""
    now = datetime.now(UTC)
    clock = DeterministicClock(initial_time=now)

    expires_at = now + timedelta(hours=1)
    content = MemoryContent(text="Temporary session note")
    mem = Memory(owner_id="owner_1", content=content, expires_at=expires_at)

    # Before expiration
    assert mem.is_expired(clock.now()) is False

    # Advance clock by 2 hours
    clock.advance(hours=2)
    assert mem.is_expired(clock.now()) is True
