"""Request ID / Correlation ID context management and ASGI middleware."""

import re
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER: str = "X-Request-ID"
_DEFAULT_REQUEST_ID: str = "unknown"

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default=_DEFAULT_REQUEST_ID)
_VALID_REQUEST_ID_REGEX: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


def get_request_id() -> str:
    """Retrieve the current request ID from context variable."""
    return _request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """Set the current request ID in context variable."""
    _request_id_ctx.set(request_id)


def generate_request_id() -> str:
    """Generate a secure UUID4 string for request tracing."""
    return str(uuid.uuid4())


def is_valid_request_id(req_id: str | None) -> bool:
    """Validate incoming request ID header format."""
    if not req_id:
        return False
    return bool(_VALID_REQUEST_ID_REGEX.match(req_id))


class RequestIDMiddleware(BaseHTTPMiddleware):
    """ASGI middleware for extracting or generating request correlation IDs."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming_id = request.headers.get(REQUEST_ID_HEADER)

        if is_valid_request_id(incoming_id) and incoming_id is not None:
            req_id = incoming_id
        else:
            req_id = generate_request_id()

        set_request_id(req_id)
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = req_id
        return response
