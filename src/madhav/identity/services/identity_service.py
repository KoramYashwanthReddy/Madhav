"""Identity & Personal Profile service business logic layer."""

import logging
import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from madhav.config.settings import get_settings
from madhav.identity.domain.assistant import AssistantIdentity
from madhav.identity.domain.context import IdentityContext
from madhav.identity.domain.owner import OwnerIdentity
from madhav.identity.domain.preferences import (
    CommunicationPreferences,
    LocalePreferences,
    UserPreferences,
)
from madhav.identity.domain.profile import PersonalProfile
from madhav.identity.exceptions import InvalidPreferenceError, InvalidProfileError
from madhav.identity.repositories.base import IdentityRepository
from madhav.identity.repositories.memory import InMemoryIdentityRepository
from madhav.identity.schemas.assistant import AssistantIdentityUpdate
from madhav.identity.schemas.owner import OwnerIdentityUpdate, SafeIdentitySummary
from madhav.identity.schemas.preferences import (
    CommunicationPreferencesUpdate,
    LocalePreferencesUpdate,
    UserPreferencesUpdate,
)
from madhav.identity.schemas.profile import PersonalProfileUpdate, ProfileCompletenessResponse

logger = logging.getLogger("madhav.identity.service")

# Regular expression for email validation
_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_RECOMMENDED_OWNER_FIELDS = [
    "display_name",
    "preferred_name",
    "email",
    "timezone",
    "locale",
    "language",
    "country",
    "city",
    "occupation",
    "bio",
]


class IdentityService:
    """Service orchestrating Identity & Personal Profile business operations."""

    def __init__(self, repository: IdentityRepository | None = None) -> None:
        self._repo: IdentityRepository = repository or InMemoryIdentityRepository()
        self._settings = get_settings()

    async def get_assistant(self) -> AssistantIdentity:
        """Retrieve active assistant identity."""
        assistant = await self._repo.get_assistant()
        if hasattr(self._settings, "identity") and self._settings.identity.assistant_name:
            assistant.name = self._settings.identity.assistant_name
        return assistant

    async def update_assistant(self, update: AssistantIdentityUpdate) -> AssistantIdentity:
        """Update assistant identity fields."""
        assistant = await self._repo.get_assistant()
        update_data = update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if value is not None:
                setattr(assistant, key, value)

        assistant.updated_at = datetime.now(UTC)
        saved = await self._repo.save_assistant(assistant)
        logger.info("Updated assistant identity: id=%s", saved.id)
        return saved

    async def get_owner(self) -> OwnerIdentity:
        """Retrieve active owner identity."""
        return await self._repo.get_owner()

    async def update_owner(self, update: OwnerIdentityUpdate) -> OwnerIdentity:
        """Update owner identity fields with validation."""
        owner = await self._repo.get_owner()
        update_data = update.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"]:
            self._validate_email(update_data["email"])
        if "timezone" in update_data and update_data["timezone"]:
            self._validate_timezone(update_data["timezone"])
        if "locale" in update_data and update_data["locale"]:
            self._validate_locale(update_data["locale"])

        for key, value in update_data.items():
            setattr(owner, key, value)

        owner.updated_at = datetime.now(UTC)
        saved = await self._repo.save_owner(owner)
        logger.info("Updated owner identity: owner_id=%s", saved.owner_id)
        return saved

    async def get_profile(self) -> PersonalProfile:
        """Retrieve complete personal profile."""
        return await self._repo.get_profile()

    async def update_profile(self, update: PersonalProfileUpdate) -> PersonalProfile:
        """Update personal profile sections atomically."""
        profile = await self._repo.get_profile()

        if update.identity:
            owner_update = await self.update_owner(update.identity)
            profile.identity = owner_update

        if update.preferences:
            profile.preferences = await self.update_user_preferences(update.preferences)

        if update.communication_preferences:
            profile.communication_preferences = await self.update_communication_preferences(
                update.communication_preferences
            )

        if update.locale_preferences:
            profile.locale_preferences = await self.update_locale_preferences(
                update.locale_preferences
            )

        if update.metadata is not None:
            profile.metadata.update(update.metadata)

        saved = await self._repo.save_profile(profile)
        logger.info("Updated personal profile for owner_id=%s", saved.identity.owner_id)
        return saved

    async def update_user_preferences(self, update: UserPreferencesUpdate) -> UserPreferences:
        """Update user interaction preferences."""
        profile = await self._repo.get_profile()
        prefs = profile.preferences
        update_data = update.model_dump(exclude_unset=True)

        if "preferred_timezone" in update_data and update_data["preferred_timezone"]:
            self._validate_timezone(update_data["preferred_timezone"])

        for key, value in update_data.items():
            if value is not None:
                setattr(prefs, key, value)

        profile.preferences = prefs
        await self._repo.save_profile(profile)
        logger.info("Updated user preferences for owner_id=%s", profile.identity.owner_id)
        return prefs

    async def update_communication_preferences(
        self, update: CommunicationPreferencesUpdate
    ) -> CommunicationPreferences:
        """Update communication channel and quiet hours preferences."""
        profile = await self._repo.get_profile()
        comm = profile.communication_preferences
        update_data = update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if value is not None:
                setattr(comm, key, value)

        profile.communication_preferences = comm
        await self._repo.save_profile(profile)
        logger.info("Updated communication preferences for owner_id=%s", profile.identity.owner_id)
        return comm

    async def update_locale_preferences(self, update: LocalePreferencesUpdate) -> LocalePreferences:
        """Update regional and locale preferences."""
        profile = await self._repo.get_profile()
        loc = profile.locale_preferences
        update_data = update.model_dump(exclude_unset=True)

        if "timezone" in update_data and update_data["timezone"]:
            self._validate_timezone(update_data["timezone"])
        if "locale" in update_data and update_data["locale"]:
            self._validate_locale(update_data["locale"])

        for key, value in update_data.items():
            if value is not None:
                setattr(loc, key, value)

        profile.locale_preferences = loc

        # Keep owner identity synced with locale preferences
        if update_data.get("timezone"):
            profile.identity.timezone = update_data["timezone"]
        if update_data.get("locale"):
            profile.identity.locale = update_data["locale"]
        if update_data.get("language"):
            profile.identity.language = update_data["language"]

        await self._repo.save_profile(profile)
        logger.info("Updated locale preferences for owner_id=%s", profile.identity.owner_id)
        return loc

    async def calculate_completeness(self) -> ProfileCompletenessResponse:
        """Calculate deterministic profile completeness score percentage (0-100%)."""
        owner = await self.get_owner()
        completed: list[str] = []
        missing: list[str] = []

        for field in _RECOMMENDED_OWNER_FIELDS:
            val = getattr(owner, field, None)
            if val is not None and str(val).strip() != "":
                completed.append(field)
            else:
                missing.append(field)

        score = int((len(completed) / len(_RECOMMENDED_OWNER_FIELDS)) * 100)
        return ProfileCompletenessResponse(
            completion_percentage=score,
            completed_fields=completed,
            missing_recommended_fields=missing,
        )

    async def get_summary(self) -> SafeIdentitySummary:
        """Return non-sensitive safe identity summary."""
        owner = await self.get_owner()
        completeness = await self.calculate_completeness()

        name = owner.preferred_name or owner.display_name or "Owner"
        tz = owner.timezone or "UTC"
        locale = owner.locale or "en_US"
        lang = owner.language or "en"

        return SafeIdentitySummary(
            owner_id=owner.owner_id,
            preferred_name=name,
            timezone=tz,
            locale=locale,
            language=lang,
            completion_percentage=completeness.completion_percentage,
        )

    async def build_identity_context(self) -> IdentityContext:
        """Construct IdentityContext domain contract for downstream module consumption."""
        assistant = await self.get_assistant()
        profile = await self.get_profile()
        return IdentityContext(
            assistant=assistant,
            owner=profile.identity,
            profile=profile,
        )

    def _validate_timezone(self, tz_str: str) -> None:
        """Validate IANA timezone identifier string."""
        if not tz_str or not isinstance(tz_str, str):
            raise InvalidPreferenceError(
                "Timezone string cannot be empty.", details={"timezone": tz_str}
            )
        try:
            ZoneInfo(tz_str)
        except ZoneInfoNotFoundError as exc:
            raise InvalidPreferenceError(
                f"Invalid IANA timezone identifier: {tz_str}",
                details={"timezone": tz_str},
            ) from exc

    def _validate_email(self, email_str: str) -> None:
        """Validate email format."""
        if not _EMAIL_REGEX.match(email_str):
            raise InvalidProfileError(
                f"Invalid email address format: {email_str}",
                details={"email": email_str},
            )

    def _validate_locale(self, locale_str: str) -> None:
        """Validate basic locale identifier string."""
        if not locale_str or len(locale_str) < 2:
            raise InvalidPreferenceError(
                f"Invalid locale identifier string: {locale_str}",
                details={"locale": locale_str},
            )
