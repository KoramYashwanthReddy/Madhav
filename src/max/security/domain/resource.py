"""Domain models for security resources."""

from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import ResourceSensitivity


class PermissionResource(BaseModel):
    """Resource specification targeted by an action request."""

    resource_type: str = Field(
        ..., description="Type identifier (FILE, TERMINAL, BROWSER, DATABASE, etc.)"
    )
    resource_id: str = Field(..., description="Unique resource key or target path")
    location: str | None = Field(default=None, description="Resource URI, directory path, or URL")
    owner_id: str = Field(..., description="Owner identity of the target resource")
    sensitivity: ResourceSensitivity = Field(
        default=ResourceSensitivity.NORMAL, description="Data sensitivity classification"
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Resource metadata attributes"
    )
