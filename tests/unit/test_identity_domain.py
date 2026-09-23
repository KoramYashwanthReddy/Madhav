"""Unit tests for Identity domain models, context, and exceptions."""

from max.identity.domain.assistant import AssistantIdentity
from max.identity.domain.context import IdentityContext
from max.identity.domain.enums import ConfirmationPreference, ResponseStyle, Verbosity
from max.identity.domain.owner import OwnerIdentity
from max.identity.domain.preferences import (
    CommunicationPreferences,
    LocalePreferences,
    UserPreferences,
)
from max.identity.domain.profile import PersonalProfile
from max.identity.exceptions import (
    IdentityNotFoundError,
    InvalidPreferenceError,
    InvalidProfileError,
)


def test_assistant_identity_defaults() -> None:
    """Verify default values for assistant identity."""
    assistant = AssistantIdentity()
    assert assistant.name == "Max"
    assert assistant.display_name == "MAX Personal AI"
    assert len(assistant.id) > 0
    assert "Platform Foundation" in assistant.capabilities_summary


def test_owner_identity_partial_support() -> None:
    """Verify OwnerIdentity allows partial/unconfigured profile fields."""
    owner = OwnerIdentity()
    assert len(owner.owner_id) > 0
    assert owner.display_name is None
    assert owner.email is None
    assert owner.timezone == "UTC"

    configured_owner = OwnerIdentity(
        display_name="Max Owner",
        preferred_name="Max User",
        email="user@example.com",
        timezone="Asia/Kolkata",
    )
    assert configured_owner.display_name == "Max Owner"
    assert configured_owner.timezone == "Asia/Kolkata"


def test_user_preferences_enums() -> None:
    """Verify UserPreferences default enum assignments."""
    prefs = UserPreferences()
    assert prefs.preferred_response_style == ResponseStyle.BALANCED
    assert prefs.confirmation_preference == ConfirmationPreference.SENSITIVE_ACTIONS
    assert prefs.verbosity_preference == Verbosity.MEDIUM


def test_personal_profile_composition() -> None:
    """Verify PersonalProfile model composition."""
    profile = PersonalProfile(
        identity=OwnerIdentity(preferred_name="Alice"),
        preferences=UserPreferences(preferred_response_style=ResponseStyle.DETAILED),
        communication_preferences=CommunicationPreferences(proactive_enabled=True),
        locale_preferences=LocalePreferences(locale="en_GB"),
    )
    assert profile.identity.preferred_name == "Alice"
    assert profile.preferences.preferred_response_style == ResponseStyle.DETAILED
    assert profile.communication_preferences.proactive_enabled is True
    assert profile.locale_preferences.locale == "en_GB"


def test_identity_context_contract() -> None:
    """Verify IdentityContext domain contract and fallback properties."""
    assistant = AssistantIdentity()
    owner_empty = OwnerIdentity()
    profile_empty = PersonalProfile(identity=owner_empty)

    ctx_empty = IdentityContext(assistant=assistant, owner=owner_empty, profile=profile_empty)
    assert ctx_empty.owner_name == "Owner"

    owner_named = OwnerIdentity(preferred_name="Bob")
    profile_named = PersonalProfile(identity=owner_named)
    ctx_named = IdentityContext(assistant=assistant, owner=owner_named, profile=profile_named)
    assert ctx_named.owner_name == "Bob"


def test_custom_identity_exceptions() -> None:
    """Verify custom exception inheritance and status codes."""
    nf_err = IdentityNotFoundError("Not found")
    assert nf_err.status_code == 404
    assert nf_err.code == "IDENTITY_NOT_FOUND"

    profile_err = InvalidProfileError("Invalid email format")
    assert profile_err.status_code == 400
    assert profile_err.code == "INVALID_PROFILE"

    pref_err = InvalidPreferenceError("Invalid timezone")
    assert pref_err.status_code == 400
    assert pref_err.code == "INVALID_PREFERENCE"
