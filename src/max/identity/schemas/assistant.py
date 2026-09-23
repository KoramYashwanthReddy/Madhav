"""Assistant identity schemas and DTOs."""

from datetime import datetime

from pydantic import BaseModel, Field


class AssistantIdentityResponse(BaseModel):
    """API response model for assistant identity."""

    id: str = Field(description="Unique assistant identifier")
    name: str = Field(description="Canonical assistant name")
    display_name: str = Field(description="Display name")
    version: str = Field(description="Software version")
    description: str = Field(description="Identity description")
    purpose: str = Field(description="Mission purpose")
    personality_profile: str = Field(description="Personality summary")
    capabilities_summary: list[str] = Field(description="Capabilities list")
    created_at: datetime = Field(description="Creation UTC timestamp")
    updated_at: datetime = Field(description="Update UTC timestamp")


class AssistantIdentityUpdate(BaseModel):
    """API request model for updating assistant identity."""

    display_name: str | None = Field(default=None, description="Updated display name")
    description: str | None = Field(default=None, description="Updated description")
    purpose: str | None = Field(default=None, description="Updated purpose")
    personality_profile: str | None = Field(default=None, description="Updated personality profile")
