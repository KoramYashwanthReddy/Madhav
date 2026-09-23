"""Identity schemas package exports."""

from max.identity.schemas.assistant import (
    AssistantIdentityResponse,
    AssistantIdentityUpdate,
)
from max.identity.schemas.owner import (
    OwnerIdentityResponse,
    OwnerIdentityUpdate,
    SafeIdentitySummary,
)
from max.identity.schemas.preferences import (
    CommunicationPreferencesResponse,
    CommunicationPreferencesUpdate,
    LocalePreferencesResponse,
    LocalePreferencesUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from max.identity.schemas.profile import (
    PersonalProfileResponse,
    PersonalProfileUpdate,
    ProfileCompletenessResponse,
)

__all__ = [
    "AssistantIdentityResponse",
    "AssistantIdentityUpdate",
    "OwnerIdentityResponse",
    "OwnerIdentityUpdate",
    "SafeIdentitySummary",
    "UserPreferencesResponse",
    "UserPreferencesUpdate",
    "CommunicationPreferencesResponse",
    "CommunicationPreferencesUpdate",
    "LocalePreferencesResponse",
    "LocalePreferencesUpdate",
    "PersonalProfileResponse",
    "PersonalProfileUpdate",
    "ProfileCompletenessResponse",
]
