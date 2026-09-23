"""Owner identity domain model."""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class OwnerIdentity(BaseModel):
    """Formal identity representation of the primary owner served by MAX."""

    owner_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique owner identifier"
    )
    display_name: str | None = Field(default=None, description="Full display name of owner")
    preferred_name: str | None = Field(
        default=None, description="Preferred name/nickname for interactions"
    )
    email: str | None = Field(default=None, description="Owner contact email address")
    phone: str | None = Field(default=None, description="Owner contact phone number")
    date_of_birth: str | None = Field(default=None, description="Date of birth (YYYY-MM-DD)")
    timezone: str | None = Field(
        default="UTC", description="IANA timezone identifier (e.g. Asia/Kolkata)"
    )
    locale: str | None = Field(
        default="en_US", description="BCP 47 / POSIX locale string (e.g. en_US)"
    )
    country: str | None = Field(default=None, description="Country of residence")
    city: str | None = Field(default=None, description="City of residence")
    language: str | None = Field(default="en", description="Primary interaction language")
    occupation: str | None = Field(default=None, description="Owner profession or occupation")
    bio: str | None = Field(default=None, description="Short bio or personal notes")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Owner identity creation UTC timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Owner identity last update UTC timestamp",
    )
