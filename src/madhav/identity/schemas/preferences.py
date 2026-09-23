"""Preference schemas and DTOs."""

from pydantic import BaseModel, Field

from madhav.identity.domain.enums import (
    CommunicationChannel,
    ConfirmationPreference,
    ResponseStyle,
    Verbosity,
)


class UserPreferencesResponse(BaseModel):
    """API response model for user preferences."""

    preferred_response_style: ResponseStyle = Field(description="Response style preference")
    preferred_language: str = Field(description="Language preference")
    preferred_timezone: str = Field(description="Timezone preference")
    preferred_date_format: str = Field(description="Date format preference")
    preferred_time_format: str = Field(description="Time format preference")
    confirmation_preference: ConfirmationPreference = Field(
        description="Action confirmation threshold"
    )
    notification_preference: str = Field(description="Notification style")
    verbosity_preference: Verbosity = Field(description="Verbosity level preference")


class UserPreferencesUpdate(BaseModel):
    """API request model for updating user preferences."""

    preferred_response_style: ResponseStyle | None = Field(
        default=None, description="Response style"
    )
    preferred_language: str | None = Field(default=None, description="Preferred language")
    preferred_timezone: str | None = Field(default=None, description="Preferred timezone")
    preferred_date_format: str | None = Field(default=None, description="Date format")
    preferred_time_format: str | None = Field(default=None, description="Time format")
    confirmation_preference: ConfirmationPreference | None = Field(
        default=None, description="Confirmation preference"
    )
    notification_preference: str | None = Field(default=None, description="Notification preference")
    verbosity_preference: Verbosity | None = Field(default=None, description="Verbosity preference")


class CommunicationPreferencesResponse(BaseModel):
    """API response model for communication preferences."""

    preferred_channel: CommunicationChannel = Field(description="Primary communication channel")
    response_style: ResponseStyle = Field(description="Response style for communications")
    proactive_enabled: bool = Field(description="Proactive communications toggle")
    quiet_hours_enabled: bool = Field(description="Quiet hours window toggle")
    quiet_hours_start: str | None = Field(description="Quiet hours start time (HH:MM)")
    quiet_hours_end: str | None = Field(description="Quiet hours end time (HH:MM)")


class CommunicationPreferencesUpdate(BaseModel):
    """API request model for updating communication preferences."""

    preferred_channel: CommunicationChannel | None = Field(
        default=None, description="Communication channel"
    )
    response_style: ResponseStyle | None = Field(default=None, description="Response style")
    proactive_enabled: bool | None = Field(
        default=None, description="Proactive communications toggle"
    )
    quiet_hours_enabled: bool | None = Field(default=None, description="Quiet hours toggle")
    quiet_hours_start: str | None = Field(default=None, description="Quiet hours start time")
    quiet_hours_end: str | None = Field(default=None, description="Quiet hours end time")


class LocalePreferencesResponse(BaseModel):
    """API response model for locale preferences."""

    timezone: str = Field(description="IANA timezone identifier")
    locale: str = Field(description="BCP 47 locale tag")
    language: str = Field(description="Language ISO code")
    country: str | None = Field(description="Country ISO code")
    date_format: str = Field(description="Regional date format")
    time_format: str = Field(description="Regional time format")
    week_start_day: str = Field(description="First day of the week")


class LocalePreferencesUpdate(BaseModel):
    """API request model for updating locale preferences."""

    timezone: str | None = Field(default=None, description="IANA timezone identifier")
    locale: str | None = Field(default=None, description="BCP 47 locale tag")
    language: str | None = Field(default=None, description="Language ISO code")
    country: str | None = Field(default=None, description="Country ISO code")
    date_format: str | None = Field(default=None, description="Date format")
    time_format: str | None = Field(default=None, description="Time format")
    week_start_day: str | None = Field(default=None, description="First day of the week")
