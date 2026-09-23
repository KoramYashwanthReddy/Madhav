"""Model repository abstraction and in-memory repository implementation."""

import asyncio
from typing import Protocol, runtime_checkable

from max.models.domain.model import Model


@runtime_checkable
class ModelRepository(Protocol):
    """Protocol contract for Model metadata persistence repositories."""

    async def save(self, model: Model) -> Model:
        """Save or update a Model definition in the repository."""
        ...

    async def get(self, model_id: str) -> Model | None:
        """Retrieve a Model definition by model_id."""
        ...

    async def list_all(self) -> list[Model]:
        """Retrieve all registered Model definitions."""
        ...

    async def delete(self, model_id: str) -> bool:
        """Delete a Model registration from the repository."""
        ...

    async def exists(self, model_id: str) -> bool:
        """Check if a model exists in the repository."""
        ...


class InMemoryModelRepository:
    """Thread-safe, async-friendly in-memory model repository implementation."""

    def __init__(self) -> None:
        self._models: dict[str, Model] = {}
        self._lock = asyncio.Lock()

    async def save(self, model: Model) -> Model:
        """Save or update a Model definition in memory."""
        async with self._lock:
            self._models[model.model_id] = model
            return model

    async def get(self, model_id: str) -> Model | None:
        """Retrieve a Model definition by model_id."""
        async with self._lock:
            return self._models.get(model_id)

    async def list_all(self) -> list[Model]:
        """Retrieve all registered Model definitions."""
        async with self._lock:
            return list(self._models.values())

    async def delete(self, model_id: str) -> bool:
        """Delete a Model registration from memory."""
        async with self._lock:
            if model_id in self._models:
                del self._models[model_id]
                return True
            return False

    async def exists(self, model_id: str) -> bool:
        """Check if a model exists in memory."""
        async with self._lock:
            return model_id in self._models
