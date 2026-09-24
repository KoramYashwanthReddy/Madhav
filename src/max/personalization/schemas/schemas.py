"""Pydantic schemas for Module 31 — Learning & Personalization Engine REST API."""

from typing import Any

from pydantic import BaseModel, Field

from max.personalization.domain.enums import PreferenceSource


class PreferenceCreateRequest(BaseModel):
    """Payload to explicitly create a user preference."""

    category: str = Field(default="COMMUNICATION", description="Preference category, e.g., COMMUNICATION")
    key: str = Field(description="Preference key name")
    value: Any = Field(description="Preference value")
    source: PreferenceSource = Field(default=PreferenceSource.EXPLICIT_USER)
    scope: str = Field(default="GLOBAL")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PreferenceUpdateRequest(BaseModel):
    """Payload to update an existing preference value."""

    value: Any = Field(description="New preference value")


class PreferenceCorrectRequest(BaseModel):
    """Payload to explicitly correct a preference."""

    correct_value: Any = Field(description="Correct value requested by user")
    comments: str | None = Field(default=None, description="Optional explanation for correction")


class FeedbackCreateRequest(BaseModel):
    """Payload to record user personalization feedback."""

    preference_id: str | None = Field(default=None)
    hypothesis_id: str | None = Field(default=None)
    feedback_type: str = Field(description="YES, NO, TOO_SHORT, TOO_LONG, INCORRECT, etc.")
    comments: str | None = Field(default=None)


class SettingsUpdateRequest(BaseModel):
    """Payload to update learning and personalization settings."""

    learning_enabled: bool | None = Field(default=None)
    personalization_enabled: bool | None = Field(default=None)
    mode: str | None = Field(default=None, description="OFF, EXPLICIT_ONLY, ASSISTED, ADAPTIVE")
    disabled_categories: list[str] | None = Field(default=None)


class ResetCategoryRequest(BaseModel):
    """Payload to reset all preferences in a category."""

    category: str = Field(description="Target category to reset")


class SignalIngestRequest(BaseModel):
    """Payload to ingest a raw learning signal."""

    source: str = Field(default="CONVERSATION")
    signal_type: str = Field(description="Signal event type key")
    payload_reference: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StatusResponse(BaseModel):
    """Generic status response DTO."""

    success: bool = Field(default=True)
    message: str = Field(default="Operation completed successfully")
    details: dict[str, Any] = Field(default_factory=dict)
