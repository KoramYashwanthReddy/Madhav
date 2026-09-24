"""Unit tests for PostgreSQL Database Infrastructure Manager."""

import pytest

from max.infrastructure.database import DatabaseManager, get_database_manager


@pytest.mark.asyncio
async def test_database_manager_health() -> None:
    db_mgr = DatabaseManager()
    health = await db_mgr.check_health()

    assert health["status"] == "ok"
    assert health["provider"] == "postgresql"
    assert health["connected"] is True
    assert health["pool_size"] == 10
    assert health["max_connections"] == 20
    assert "latency_ms" in health


@pytest.mark.asyncio
async def test_database_manager_degraded_state() -> None:
    db_mgr = DatabaseManager()
    db_mgr.set_connected_state(False)
    health = await db_mgr.check_health()

    assert health["status"] == "error"
    assert health["connected"] is False


def test_database_dump_command_args() -> None:
    db_mgr = DatabaseManager()
    args = db_mgr.get_dump_command_args()
    assert args[0] == "pg_dump"
    assert "--format=custom" in args


def test_get_database_manager_singleton() -> None:
    m1 = get_database_manager()
    m2 = get_database_manager()
    assert m1 is m2
