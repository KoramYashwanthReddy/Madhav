"""Domain preference models for User, Communication, and Locale preferences."""

from pydantic import BaseModel, Field

from madhav.identity.domain.enums import (
    CommunicationChannel,
    ConfirmationPreference,
    ResponseStyle,
    Verbosity,
)


class UserPreferences(BaseModel):
    """General interaction preferences of the owner."""

    preferred_response_style: ResponseStyle = Field(
        default=ResponseStyle.BALANCED, description="Preferred response style"
    )
    preferred_language: str = Field(default="en", description="Preferred interaction language code")
    preferred_timezone: str = Field(default="UTC", description="Preferred timezone identifier")
    preferred_date_format: str = Field(
        default="YYYY-MM-DD", description="Preferred date display format"
    )
    preferred_time_format: str = Field(
        default="24h", description="Preferred time display format (12h/24h)"
    )
    confirmation_preference: ConfirmationPreference = Field(
        default=ConfirmationPreference.SENSITIVE_ACTIONS,
        description="Action confirmation threshold preference",
    )
    notification_preference: str = Field(default="normal", description="Notification alert style")
    verbosity_preference: Verbosity = Field(
        default=Verbosity.MEDIUM, description="Explanation verbosity preference"
    )


class CommunicationPreferences(BaseModel):
    """Communication channel and quiet hours preferences."""

    preferred_channel: CommunicationChannel = Field(
        default=CommunicationChannel.TEXT, description="Primary communication channel"
    )
    response_style: ResponseStyle = Field(
        default=ResponseStyle.BALANCED, description="Default response style for communication"
    )
    proactive_enabled: bool = Field(
        default=False, description="Allow proactive assistant communications"
    )
    quiet_hours_enabled: bool = Field(
        default=False, description="Enable quiet hours restriction window"
    )
    quiet_hours_start: str | None = Field(
        default="22:00", description="Quiet hours start time (HH:MM)"
    )
    quiet_hours_end: str | None = Field(default="07:00", description="Quiet hours end time (HH:MM)")


class LocalePreferences(BaseModel):
    """Locale, regional, and time formatting preferences."""

    timezone: str = Field(default="UTC", description="IANA timezone string")
    locale: str = Field(default="en_US", description="BCP 47 locale tag")
    language: str = Field(default="en", description="Primary language ISO code")
    country: str | None = Field(default=None, description="Country code (ISO 3166-1 alpha-2)")
    date_format: str = Field(default="YYYY-MM-DD", description="Regional date display format")
    time_format: str = Field(default="24h", description="Regional time display format")
    week_start_day: str = Field(default="Monday", description="First day of the week")
