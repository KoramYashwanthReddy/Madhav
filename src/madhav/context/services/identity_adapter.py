"""Privacy-aware IdentityContext adapter projecting safe identity fields into ContextItems."""


from madhav.context.domain.enums import ContextCategory, ContextPriority, SourceTrustLevel
from madhav.context.domain.item import ContextItem
from madhav.identity.domain.context import IdentityContext


class IdentityProjection:
    """Projects Module 03 IdentityContext into privacy-filtered ContextItem objects."""

    @classmethod
    def project(
        cls, identity_context: IdentityContext, allow_sensitive: bool = False
    ) -> list[ContextItem]:
        """Convert IdentityContext into safe context items based on privacy policy rules."""
        items: list[ContextItem] = []

        # 1. Assistant Identity (Safe public instructions)
        assistant = identity_context.assistant
        assistant_content = (
            f"Assistant Identity:\n"
            f"Name: {assistant.name} ({assistant.display_name})\n"
            f"Purpose: {assistant.purpose}\n"
            f"Personality: {assistant.personality_profile}"
        )
        items.append(
            ContextItem(
                category=ContextCategory.IDENTITY,
                content=assistant_content,
                priority=ContextPriority.HIGH,
                required=False,
                source="identity_assistant",
                trust_level=SourceTrustLevel.TRUSTED,
                metadata={"scope": "assistant", "sensitive": False},
            )
        )

        # 2. Owner Safe Identity (Non-sensitive interaction details)
        owner = identity_context.owner
        owner_name = identity_context.owner_name
        owner_safe_parts = [f"Owner Name: {owner_name}"]
        if owner.language:
            owner_safe_parts.append(f"Language: {owner.language}")
        if owner.timezone:
            owner_safe_parts.append(f"Timezone: {owner.timezone}")
        if owner.locale:
            owner_safe_parts.append(f"Locale: {owner.locale}")

        owner_safe_content = "Owner Preferences:\n" + "\n".join(owner_safe_parts)
        items.append(
            ContextItem(
                category=ContextCategory.IDENTITY,
                content=owner_safe_content,
                priority=ContextPriority.HIGH,
                required=False,
                source="identity_owner_safe",
                trust_level=SourceTrustLevel.TRUSTED,
                metadata={"scope": "owner_safe", "sensitive": False},
            )
        )

        # 3. Personal Profile Summary (Safe preferences)
        profile = identity_context.profile
        if profile:
            comm_parts = []
            if profile.preferences:
                comm_parts.append(f"Style: {profile.preferences.preferred_response_style}")
                comm_parts.append(f"Verbosity: {profile.preferences.verbosity_preference}")
            if profile.communication_preferences:
                comm_parts.append(f"Channel: {profile.communication_preferences.preferred_channel}")

            if comm_parts:
                items.append(
                    ContextItem(
                        category=ContextCategory.IDENTITY,
                        content="Communication Style:\n" + "\n".join(comm_parts),
                        priority=ContextPriority.NORMAL,
                        required=False,
                        source="identity_profile_preferences",
                        trust_level=SourceTrustLevel.TRUSTED,
                        metadata={"scope": "preferences", "sensitive": False},
                    )
                )


        # 4. Sensitive Owner Details (Included ONLY if explicit policy permits)
        if allow_sensitive:
            sensitive_parts = []
            if owner.email:
                sensitive_parts.append(f"Email: {owner.email}")
            if owner.phone:
                sensitive_parts.append(f"Phone: {owner.phone}")
            if owner.date_of_birth:
                sensitive_parts.append(f"Date of Birth: {owner.date_of_birth}")
            if owner.country:
                sensitive_parts.append(f"Country: {owner.country}")
            if owner.city:
                sensitive_parts.append(f"City: {owner.city}")
            if owner.occupation:
                sensitive_parts.append(f"Occupation: {owner.occupation}")

            if sensitive_parts:
                items.append(
                    ContextItem(
                        category=ContextCategory.IDENTITY,
                        content="Sensitive Owner Identity Details:\n" + "\n".join(sensitive_parts),
                        priority=ContextPriority.LOW,
                        required=False,
                        source="identity_owner_sensitive",
                        trust_level=SourceTrustLevel.TRUSTED,
                        metadata={"scope": "owner_sensitive", "sensitive": True},
                    )
                )

        return items
