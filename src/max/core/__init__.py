"""Core foundation modules for MAX platform."""

from max.core.exceptions import (
    ApplicationError,
    InternalError,
    MaxException,
    NotFoundError,
    ValidationError,
)
from max.core.request_id import get_request_id, set_request_id
from max.core.responses import APIResponse, ErrorDetails, ErrorResponse

__all__ = [
    "MaxException",
    "ApplicationError",
    "ValidationError",
    "NotFoundError",
    "InternalError",
    "APIResponse",
    "ErrorDetails",
    "ErrorResponse",
    "get_request_id",
    "set_request_id",
]
