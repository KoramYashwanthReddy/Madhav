"""Identity repository package exports."""

from max.identity.repositories.base import IdentityRepository
from max.identity.repositories.memory import InMemoryIdentityRepository

__all__ = ["IdentityRepository", "InMemoryIdentityRepository"]
