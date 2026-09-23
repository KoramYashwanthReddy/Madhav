"""Unit tests for exception architecture and centralized error handlers."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from madhav.core.error_handlers import register_exception_handlers
from madhav.core.exceptions import (
    ApplicationError,
    InternalError,
    MadhavException,
    NotFoundError,
    ValidationError,
)
from madhav.core.request_id import RequestIDMiddleware


def test_exception_classes_hierarchy() -> None:
    """Verify custom exception attributes and default status codes."""
    base_exc = MadhavException("Custom error", code="CUSTOM_CODE", status_code=418)
    assert base_exc.message == "Custom error"
    assert base_exc.code == "CUSTOM_CODE"
    assert base_exc.status_code == 418

    app_exc = ApplicationError("App error")
    assert app_exc.code == "APPLICATION_ERROR"
    assert app_exc.status_code == 400

    val_exc = ValidationError("Validation error")
    assert val_exc.code == "VALIDATION_ERROR"
    assert val_exc.status_code == 400

    nf_exc = NotFoundError("Not found error")
    assert nf_exc.code == "NOT_FOUND"
    assert nf_exc.status_code == 404

    int_exc = InternalError("Internal error")
    assert int_exc.code == "INTERNAL_ERROR"
    assert int_exc.status_code == 500


@pytest.mark.asyncio
async def test_custom_exception_handler_response() -> None:
    """Test custom MadhavException handled into standard ErrorResponse structure."""
    test_app = FastAPI()
    test_app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(test_app)

    @test_app.get("/test-error")
    async def trigger_error() -> None:
        raise NotFoundError("Test item was not found")

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        res = await client.get("/test-error")
        assert res.status_code == 404
        data = res.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["message"] == "Test item was not found"
        assert "request_id" in data["error"]


@pytest.mark.asyncio
async def test_unhandled_exception_hides_traceback() -> None:
    """Test unhandled exceptions return 500 without leaking stack traces."""
    test_app = FastAPI()
    test_app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(test_app)

    @test_app.get("/crash")
    async def trigger_crash() -> None:
        raise ValueError("Secret database credentials exposed in raw stack trace!")

    async with AsyncClient(
        transport=ASGITransport(app=test_app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as client:
        res = await client.get("/crash")
        assert res.status_code == 500
        data = res.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert data["error"]["message"] == "An internal error occurred."
        assert "Secret database credentials" not in res.text
