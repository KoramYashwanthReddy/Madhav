"""Abstract repository interface protocol for Identity & Profile storage."""

from typing import Protocol, runtime_checkable

from max.identity.domain.assistant import AssistantIdentity
from max.identity.domain.owner import OwnerIdentity
from max.identity.domain.profile import PersonalProfile


@runtime_checkable
class IdentityRepository(Protocol):
    """Protocol defining identity storage contract."""

    async def get_assistant(self) -> AssistantIdentity:
        """Retrieve active assistant identity."""
        ...

    async def save_assistant(self, assistant: AssistantIdentity) -> AssistantIdentity:
        """Save/update assistant identity."""
        ...

    async def get_owner(self) -> OwnerIdentity:
        """Retrieve active owner identity."""
        ...

    async def save_owner(self, owner: OwnerIdentity) -> OwnerIdentity:
        """Save/update owner identity."""
        ...

    async def get_profile(self) -> PersonalProfile:
        """Retrieve complete personal profile."""
        ...

    async def save_profile(self, profile: PersonalProfile) -> PersonalProfile:
        """Save/update complete personal profile."""
        ...
