"""Personal profile schemas and completeness DTOs."""

from typing import Any

from pydantic import BaseModel, Field

from madhav.identity.schemas.owner import OwnerIdentityResponse, OwnerIdentityUpdate
from madhav.identity.schemas.preferences import (
    CommunicationPreferencesResponse,
    CommunicationPreferencesUpdate,
    LocalePreferencesResponse,
    LocalePreferencesUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)


class PersonalProfileResponse(BaseModel):
    """API response model for complete personal profile."""

    identity: OwnerIdentityResponse = Field(description="Owner identity payload")
    preferences: UserPreferencesResponse = Field(description="User preferences payload")
    communication_preferences: CommunicationPreferencesResponse = Field(
        description="Communication preferences payload"
    )
    locale_preferences: LocalePreferencesResponse = Field(description="Locale preferences payload")
    metadata: dict[str, Any] = Field(description="Metadata key-value pairs")


class PersonalProfileUpdate(BaseModel):
    """API request model for updating complete personal profile."""

    identity: OwnerIdentityUpdate | None = Field(default=None, description="Owner identity updates")
    preferences: UserPreferencesUpdate | None = Field(
        default=None, description="Preferences updates"
    )
    communication_preferences: CommunicationPreferencesUpdate | None = Field(
        default=None, description="Communication updates"
    )
    locale_preferences: LocalePreferencesUpdate | None = Field(
        default=None, description="Locale updates"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Metadata updates")


class ProfileCompletenessResponse(BaseModel):
    """API response model for profile completeness metrics."""

    completion_percentage: int = Field(description="Profile completeness score percentage (0-100%)")
    completed_fields: list[str] = Field(description="List of completed profile fields")
    missing_recommended_fields: list[str] = Field(
        description="List of recommended fields currently missing"
    )
