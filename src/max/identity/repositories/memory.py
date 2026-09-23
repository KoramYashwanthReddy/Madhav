"""Thread-safe in-memory repository implementation for Identity & Profile storage."""

import asyncio

from max.identity.domain.assistant import AssistantIdentity
from max.identity.domain.owner import OwnerIdentity
from max.identity.domain.profile import PersonalProfile


class InMemoryIdentityRepository:
    """In-memory implementation of IdentityRepository protocol."""

    def __init__(
        self,
        assistant: AssistantIdentity | None = None,
        profile: PersonalProfile | None = None,
    ) -> None:
        self._lock = asyncio.Lock()
        self._assistant = assistant or AssistantIdentity()
        self._profile = profile or PersonalProfile(identity=OwnerIdentity())

    async def get_assistant(self) -> AssistantIdentity:
        """Retrieve cached assistant identity."""
        async with self._lock:
            return self._assistant.model_copy(deep=True)

    async def save_assistant(self, assistant: AssistantIdentity) -> AssistantIdentity:
        """Save assistant identity."""
        async with self._lock:
            self._assistant = assistant.model_copy(deep=True)
            return self._assistant.model_copy(deep=True)

    async def get_owner(self) -> OwnerIdentity:
        """Retrieve cached owner identity."""
        async with self._lock:
            return self._profile.identity.model_copy(deep=True)

    async def save_owner(self, owner: OwnerIdentity) -> OwnerIdentity:
        """Save owner identity and sync within personal profile."""
        async with self._lock:
            self._profile.identity = owner.model_copy(deep=True)
            return self._profile.identity.model_copy(deep=True)

    async def get_profile(self) -> PersonalProfile:
        """Retrieve cached personal profile."""
        async with self._lock:
            return self._profile.model_copy(deep=True)

    async def save_profile(self, profile: PersonalProfile) -> PersonalProfile:
        """Save personal profile."""
        async with self._lock:
            self._profile = profile.model_copy(deep=True)
            return self._profile.model_copy(deep=True)
