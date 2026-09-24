"""Unit tests for Redis Cache & Queue Infrastructure Manager."""

import pytest
from max.infrastructure.redis import RedisManager, get_redis_manager


@pytest.mark.asyncio
async def test_redis_manager_health() -> None:
    redis_mgr = RedisManager()
    health = await redis_mgr.check_health()

    assert health["status"] == "ok"
    assert health["provider"] == "redis"
    assert health["connected"] is True
    assert "latency_ms" in health


@pytest.mark.asyncio
async def test_redis_manager_degraded_state() -> None:
    redis_mgr = RedisManager()
    redis_mgr.set_connected_state(False)
    health = await redis_mgr.check_health()

    assert health["status"] == "error"
    assert health["connected"] is False


def test_get_redis_manager_singleton() -> None:
    r1 = get_redis_manager()
    r2 = get_redis_manager()
    assert r1 is r2
