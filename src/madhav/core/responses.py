"""Standardized API response models for MADHAV platform foundation."""

from typing import Any

from pydantic import BaseModel, Field


class APIResponse[T](BaseModel):
    """Standard success API response wrapper."""

    success: bool = Field(default=True, description="Indicates request success status")
    data: T = Field(description="Payload data returned by endpoint")
    request_id: str = Field(description="Unique correlation ID for request tracing")


class ErrorDetails(BaseModel):
    """Detailed error object contained within ErrorResponse."""

    code: str = Field(description="Machine-readable error code identifier")
    message: str = Field(description="Human-readable description of error")
    details: dict[str, Any] | list[Any] | None = Field(
        default=None, description="Optional structured error metadata or context"
    )
    request_id: str = Field(description="Unique correlation ID for request tracing")


class ErrorResponse(BaseModel):
    """Standard error API response wrapper."""

    success: bool = Field(default=False, description="Indicates request failure status")
    error: ErrorDetails = Field(description="Error details payload")
