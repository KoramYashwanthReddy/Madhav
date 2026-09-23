"""Centralized exception handlers for FastAPI application."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from madhav.core.exceptions import MadhavException
from madhav.core.request_id import get_request_id
from madhav.core.responses import ErrorDetails, ErrorResponse

logger = logging.getLogger("madhav.error_handler")


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with FastAPI application instance."""

    @app.exception_handler(MadhavException)
    async def madhav_exception_handler(request: Request, exc: MadhavException) -> JSONResponse:
        req_id = get_request_id()
        logger.warning(
            "MadhavException caught: code=%s message=%s status=%d",
            exc.code,
            exc.message,
            exc.status_code,
        )
        error_payload = ErrorResponse(
            success=False,
            error=ErrorDetails(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=req_id,
            ),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload.model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        req_id = get_request_id()
        code = f"HTTP_{exc.status_code}"
        logger.warning("HTTPException caught: status=%d detail=%s", exc.status_code, exc.detail)
        error_payload = ErrorResponse(
            success=False,
            error=ErrorDetails(
                code=code,
                message=str(exc.detail),
                details=None,
                request_id=req_id,
            ),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = get_request_id()
        raw_errors: list[dict[str, Any]] = exc.errors()  # type: ignore[assignment]
        logger.warning("RequestValidationError caught: %d errors", len(raw_errors))
        error_payload = ErrorResponse(
            success=False,
            error=ErrorDetails(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=raw_errors,
                request_id=req_id,
            ),
        )
        return JSONResponse(
            status_code=400,
            content=error_payload.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = get_request_id()
        logger.exception("Unhandled exception caught during request execution")
        error_payload = ErrorResponse(
            success=False,
            error=ErrorDetails(
                code="INTERNAL_ERROR",
                message="An internal error occurred.",
                details=None,
                request_id=req_id,
            ),
        )
        return JSONResponse(
            status_code=500,
            content=error_payload.model_dump(),
        )
