"""Unit tests for IdentityService business logic and validation."""

import pytest

from madhav.identity.domain.enums import ResponseStyle
from madhav.identity.exceptions import InvalidPreferenceError, InvalidProfileError
from madhav.identity.repositories.memory import InMemoryIdentityRepository
from madhav.identity.schemas.owner import OwnerIdentityUpdate
from madhav.identity.schemas.preferences import (
    CommunicationPreferencesUpdate,
    LocalePreferencesUpdate,
    UserPreferencesUpdate,
)
from madhav.identity.services.identity_service import IdentityService


@pytest.fixture
def identity_service() -> IdentityService:
    """Fixture providing an isolated IdentityService instance."""
    repo = InMemoryIdentityRepository()
    return IdentityService(repository=repo)


@pytest.mark.asyncio
async def test_get_and_update_assistant(identity_service: IdentityService) -> None:
    """Test retrieving and updating assistant identity."""
    assistant = await identity_service.get_assistant()
    assert assistant.name == "Madhav"


@pytest.mark.asyncio
async def test_update_owner_validations(identity_service: IdentityService) -> None:
    """Test owner updates and input validation."""
    # 1. Valid update
    updated = await identity_service.update_owner(
        OwnerIdentityUpdate(
            display_name="Jane Doe",
            email="jane.doe@example.com",
            timezone="Asia/Kolkata",
            locale="en_IN",
        )
    )
    assert updated.display_name == "Jane Doe"
    assert updated.email == "jane.doe@example.com"
    assert updated.timezone == "Asia/Kolkata"

    # 2. Invalid email format
    with pytest.raises(InvalidProfileError) as exc_info:
        await identity_service.update_owner(OwnerIdentityUpdate(email="not-an-email"))
    assert "Invalid email address format" in str(exc_info.value)

    # 3. Invalid IANA timezone
    with pytest.raises(InvalidPreferenceError) as exc_info:
        await identity_service.update_owner(OwnerIdentityUpdate(timezone="Invalid/Timezone"))
    assert "Invalid IANA timezone" in str(exc_info.value)


@pytest.mark.asyncio
async def test_calculate_completeness(identity_service: IdentityService) -> None:
    """Test profile completeness score calculation."""
    empty_comp = await identity_service.calculate_completeness()
    # By default, language="en", timezone="UTC", locale="en_US" are present
    assert empty_comp.completion_percentage == 30
    assert "display_name" in empty_comp.missing_recommended_fields

    await identity_service.update_owner(
        OwnerIdentityUpdate(
            display_name="Owner Name",
            preferred_name="Owner",
            email="owner@example.com",
            timezone="America/New_York",
            locale="en_US",
            language="en",
            country="US",
            city="New York",
            occupation="Engineer",
            bio="Personal assistant owner.",
        )
    )

    full_comp = await identity_service.calculate_completeness()
    assert full_comp.completion_percentage == 100
    assert len(full_comp.missing_recommended_fields) == 0


@pytest.mark.asyncio
async def test_get_safe_summary(identity_service: IdentityService) -> None:
    """Test SafeIdentitySummary non-sensitive output generation."""
    await identity_service.update_owner(
        OwnerIdentityUpdate(
            preferred_name="Alice",
            email="alice@secret.com",
            timezone="Europe/London",
        )
    )

    summary = await identity_service.get_summary()
    assert summary.preferred_name == "Alice"
    assert summary.timezone == "Europe/London"
    assert not hasattr(summary, "email")


@pytest.mark.asyncio
async def test_update_preferences(identity_service: IdentityService) -> None:
    """Test user, communication, and locale preferences updates."""
    user_prefs = await identity_service.update_user_preferences(
        UserPreferencesUpdate(preferred_response_style=ResponseStyle.CONCISE)
    )
    assert user_prefs.preferred_response_style == ResponseStyle.CONCISE

    comm_prefs = await identity_service.update_communication_preferences(
        CommunicationPreferencesUpdate(proactive_enabled=True)
    )
    assert comm_prefs.proactive_enabled is True

    loc_prefs = await identity_service.update_locale_preferences(
        LocalePreferencesUpdate(timezone="Asia/Tokyo", locale="ja_JP")
    )
    assert loc_prefs.timezone == "Asia/Tokyo"
    assert loc_prefs.locale == "ja_JP"
