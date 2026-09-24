"""Profile service assembling structured personalization profiles for Module 31."""

import logging
from datetime import UTC, datetime

from max.personalization.domain.enums import PreferenceCategory
from max.personalization.domain.models import (
    AutonomyProfile,
    CommunicationProfile,
    NotificationProfile,
    PersonalizationProfile,
    ProactivityProfile,
)
from max.personalization.repositories.interfaces import (
    PersonalizationProfileRepository,
    PreferenceRepository,
)
from max.personalization.services.preference_resolver import PreferenceResolver

logger = logging.getLogger(__name__)


class PersonalizationProfileService:
    """Assembles and syncs structured user personalization profiles from resolved preferences."""

    def __init__(
        self,
        profile_repo: PersonalizationProfileRepository,
        preference_repo: PreferenceRepository,
        resolver: PreferenceResolver,
    ) -> None:
        self.profile_repo = profile_repo
        self.preference_repo = preference_repo
        self.resolver = resolver

    async def get_or_create_profile(self, owner_id: str = "default_owner") -> PersonalizationProfile:
        """Fetch existing user profile or build fresh structured profile from resolved preferences."""
        profile = await self.profile_repo.get_by_owner(owner_id)
        if profile is None:
            profile = PersonalizationProfile(owner_id=owner_id)
            profile = await self.sync_profile(profile)

        return profile

    async def sync_profile(self, profile: PersonalizationProfile) -> PersonalizationProfile:
        """Sync structured sub-profiles from current active preferences."""
        owner_id = profile.owner_id
        disabled_cats = profile.privacy_preferences.get("disabled_categories", [])

        # 1. Communication Profile
        comm_detail = await self.resolver.resolve(
            category=PreferenceCategory.COMMUNICATION.value,
            key="detail_level",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )
        comm_depth = await self.resolver.resolve(
            category=PreferenceCategory.COMMUNICATION.value,
            key="technical_depth",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )
        comm_length = await self.resolver.resolve(
            category=PreferenceCategory.COMMUNICATION.value,
            key="response_length",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )
        comm_tone = await self.resolver.resolve(
            category=PreferenceCategory.COMMUNICATION.value,
            key="tone",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )

        profile.communication_profile = CommunicationProfile(
            detail_level=str(comm_detail.value),
            technical_depth=str(comm_depth.value),
            response_length=str(comm_length.value),
            tone=str(comm_tone.value),
        )

        # 2. Notification Profile
        notif_freq = await self.resolver.resolve(
            category=PreferenceCategory.NOTIFICATION.value,
            key="notification_frequency",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )
        notif_thresh = await self.resolver.resolve(
            category=PreferenceCategory.NOTIFICATION.value,
            key="priority_threshold",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )

        profile.notification_profile = NotificationProfile(
            notification_frequency=str(notif_freq.value),
            priority_threshold=str(notif_thresh.value),
        )

        # 3. Proactivity Profile
        pro_mode = await self.resolver.resolve(
            category=PreferenceCategory.PROACTIVITY.value,
            key="proactive_mode",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )
        pro_thresh = await self.resolver.resolve(
            category=PreferenceCategory.PROACTIVITY.value,
            key="interruption_threshold",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )

        try:
            val_thresh = float(pro_thresh.value)
        except (ValueError, TypeError):
            val_thresh = 0.5

        profile.proactivity_profile = ProactivityProfile(
            proactive_mode=str(pro_mode.value),
            interruption_threshold=val_thresh,
        )

        # 4. Autonomy Profile
        aut_level = await self.resolver.resolve(
            category=PreferenceCategory.AUTONOMY.value,
            key="preferred_autonomy_level",
            owner_id=owner_id,
            disabled_categories=disabled_cats,
        )
        try:
            val_aut = int(aut_level.value)
        except (ValueError, TypeError):
            val_aut = 1

        profile.autonomy_profile = AutonomyProfile(
            preferred_autonomy_level=val_aut,
        )

        # 5. Active preferences map summary
        all_active = await self.preference_repo.list_by_owner(owner_id, active_only=True)
        profile.preferences = {p.key: p.value for p in all_active}
        profile.version += 1
        profile.updated_at = datetime.now(UTC)

        return await self.profile_repo.save(profile)
