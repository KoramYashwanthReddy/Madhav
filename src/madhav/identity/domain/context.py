"""IdentityContext domain contract for downstream module consumption."""

from pydantic import BaseModel, Field

from madhav.identity.domain.assistant import AssistantIdentity
from madhav.identity.domain.owner import OwnerIdentity
from madhav.identity.domain.profile import PersonalProfile


class IdentityContext(BaseModel):
    """Read-only identity context supplied to downstream AI & orchestration modules."""

    assistant: AssistantIdentity = Field(description="Active assistant identity")
    owner: OwnerIdentity = Field(description="Active owner identity")
    profile: PersonalProfile = Field(description="Active personal profile")

    @property
    def owner_name(self) -> str:
        """Convenience property returning owner preferred name or fallback."""
        if self.owner.preferred_name:
            return self.owner.preferred_name
        if self.owner.display_name:
            return self.owner.display_name
        return "Owner"
