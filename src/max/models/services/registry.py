"""Model registry providing high-level indexing and search over Model definitions."""

import logging

from max.models.domain.enums import ModelLifecycleState, ModelProvider
from max.models.domain.model import Model
from max.models.exceptions import ModelAlreadyExistsError, ModelNotFoundError
from max.models.services.repositories import ModelRepository

logger = logging.getLogger("max.models.registry")


class ModelRegistry:
    """High-level metadata registry for indexing and searching Model definitions."""

    def __init__(self, repository: ModelRepository) -> None:
        self._repository: ModelRepository = repository

    async def register_model(self, model: Model) -> Model:
        """Register a new Model definition."""
        if await self._repository.exists(model.model_id):
            logger.warning("Attempted duplicate registration for model_id: '%s'", model.model_id)
            raise ModelAlreadyExistsError(
                f"Model with identifier '{model.model_id}' is already registered.",
                details={"model_id": model.model_id},
            )

        saved = await self._repository.save(model)
        logger.info(
            "Registered model metadata: '%s' (provider: %s, target_runtime: %s)",
            model.model_id,
            model.identifier.provider,
            model.target_runtime,
        )
        return saved

    async def update_model(self, model: Model) -> Model:
        """Update an existing Model definition."""
        if not await self._repository.exists(model.model_id):
            raise ModelNotFoundError(
                f"Model with identifier '{model.model_id}' not found.",
                details={"model_id": model.model_id},
            )

        return await self._repository.save(model)

    async def get_model(self, model_id: str) -> Model:
        """Retrieve a Model definition or raise ModelNotFoundError."""
        model = await self._repository.get(model_id)
        if not model:
            raise ModelNotFoundError(
                f"Model with identifier '{model_id}' not found.",
                details={"model_id": model_id},
            )
        return model

    async def list_models(
        self,
        provider: ModelProvider | str | None = None,
        state: ModelLifecycleState | str | None = None,
        target_runtime: str | None = None,
    ) -> list[Model]:
        """List registered Model definitions with optional filtering."""
        all_models = await self._repository.list_all()
        filtered = all_models

        if provider:
            provider_str = str(provider).lower()
            filtered = [m for m in filtered if str(m.identifier.provider).lower() == provider_str]

        if state:
            state_str = str(state).lower()
            filtered = [m for m in filtered if str(m.lifecycle_state).lower() == state_str]

        if target_runtime:
            runtime_str = target_runtime.lower()
            filtered = [m for m in filtered if m.target_runtime.lower() == runtime_str]

        return filtered

    async def unregister_model(self, model_id: str) -> bool:
        """Unregister a model definition from the registry (metadata only)."""
        model = await self.get_model(model_id)
        if model.is_loaded:
            raise ValueError(
                f"Cannot unregister model '{model_id}' while it is in LOADED state. "
                "Unload model first."
            )

        deleted = await self._repository.delete(model_id)
        if deleted:
            logger.info("Unregistered model definition: '%s'", model_id)
        return deleted
