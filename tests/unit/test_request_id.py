"""Unit tests for Request ID middleware and correlation context."""

import pytest
from httpx import AsyncClient

from madhav.core.request_id import is_valid_request_id


def test_is_valid_request_id() -> None:
    """Test validation rules for incoming request ID strings."""
    assert is_valid_request_id("req-12345") is True
    assert is_valid_request_id("550e8400-e29b-41d4-a716-446655440000") is True
    assert is_valid_request_id(None) is False
    assert is_valid_request_id("") is False
    assert is_valid_request_id("a" * 65) is False
    assert is_valid_request_id("<script>alert(1)</script>") is False


@pytest.mark.asyncio
async def test_request_id_generated_if_missing(client: AsyncClient) -> None:
    """Test automatic generation of X-Request-ID header."""
    res = await client.get("/health")
    assert "X-Request-ID" in res.headers
    req_id = res.headers["X-Request-ID"]
    assert len(req_id) > 0


@pytest.mark.asyncio
async def test_request_id_propagated_if_valid(client: AsyncClient) -> None:
    """Test client-supplied X-Request-ID is preserved and echoed."""
    custom_id = "client-provided-correlation-id-999"
    res = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert res.headers["X-Request-ID"] == custom_id
    assert res.json()["request_id"] == custom_id
