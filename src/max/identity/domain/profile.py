"""Personal profile domain model composing identity and preferences."""

from typing import Any

from pydantic import BaseModel, Field

from max.identity.domain.owner import OwnerIdentity
from max.identity.domain.preferences import (
    CommunicationPreferences,
    LocalePreferences,
    UserPreferences,
)


class PersonalProfile(BaseModel):
    """Unified personal profile representing stable owner attributes and settings."""

    identity: OwnerIdentity = Field(
        default_factory=OwnerIdentity, description="Owner identity data"
    )
    preferences: UserPreferences = Field(
        default_factory=UserPreferences, description="General user preferences"
    )
    communication_preferences: CommunicationPreferences = Field(
        default_factory=CommunicationPreferences, description="Communication channel preferences"
    )
    locale_preferences: LocalePreferences = Field(
        default_factory=LocalePreferences, description="Regional and locale preferences"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Extensible metadata key-value mapping"
    )
