"""Owner identity schemas and DTOs."""

from datetime import datetime

from pydantic import BaseModel, Field


class OwnerIdentityResponse(BaseModel):
    """API response model for complete owner identity."""

    owner_id: str = Field(description="Unique owner identifier")
    display_name: str | None = Field(default=None, description="Display name")
    preferred_name: str | None = Field(default=None, description="Preferred name")
    email: str | None = Field(default=None, description="Contact email")
    phone: str | None = Field(default=None, description="Contact phone")
    date_of_birth: str | None = Field(default=None, description="Date of birth")
    timezone: str | None = Field(default=None, description="IANA timezone")
    locale: str | None = Field(default=None, description="Locale identifier")
    country: str | None = Field(default=None, description="Country code")
    city: str | None = Field(default=None, description="City name")
    language: str | None = Field(default=None, description="Language code")
    occupation: str | None = Field(default=None, description="Occupation")
    bio: str | None = Field(default=None, description="Short bio")
    created_at: datetime = Field(description="Creation UTC timestamp")
    updated_at: datetime = Field(description="Update UTC timestamp")


class OwnerIdentityUpdate(BaseModel):
    """API request model for updating owner identity."""

    display_name: str | None = Field(default=None, description="Display name")
    preferred_name: str | None = Field(default=None, description="Preferred name")
    email: str | None = Field(default=None, description="Contact email")
    phone: str | None = Field(default=None, description="Contact phone")
    date_of_birth: str | None = Field(default=None, description="Date of birth (YYYY-MM-DD)")
    timezone: str | None = Field(default=None, description="IANA timezone identifier")
    locale: str | None = Field(default=None, description="Locale string")
    country: str | None = Field(default=None, description="Country")
    city: str | None = Field(default=None, description="City")
    language: str | None = Field(default=None, description="Language")
    occupation: str | None = Field(default=None, description="Occupation")
    bio: str | None = Field(default=None, description="Bio")


class SafeIdentitySummary(BaseModel):
    """Sanitized non-sensitive identity summary suitable for diagnostics and log representation."""

    owner_id: str = Field(description="Owner identifier")
    preferred_name: str = Field(description="Preferred display name or default")
    timezone: str = Field(description="Active timezone")
    locale: str = Field(description="Active locale")
    language: str = Field(description="Active language")
    completion_percentage: int = Field(description="Profile completeness score percentage")
