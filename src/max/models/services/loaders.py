"""Model loader abstraction and development stub loader implementation."""

import asyncio
import logging
from typing import Protocol, runtime_checkable

from max.models.domain.enums import ModelLifecycleState
from max.models.domain.model import Model
from max.models.exceptions import ModelLoadError, ModelUnloadError

logger = logging.getLogger("max.models.loader")


@runtime_checkable
class ModelLoader(Protocol):
    """Protocol for provider-neutral model execution loaders."""

    async def load(self, model: Model) -> Model:
        """Load target model into operational runtime."""
        ...

    async def unload(self, model: Model) -> Model:
        """Unload target model from operational runtime."""
        ...

    async def is_loaded(self, model: Model) -> bool:
        """Check if model is currently loaded in runtime."""
        ...


class DevelopmentModelLoader:
    """Offline development stub model loader managing state transitions safely."""

    def __init__(self) -> None:
        self._loaded_models: set[str] = set()
        self._lock = asyncio.Lock()

    async def load(self, model: Model) -> Model:
        """Load development stub model into active state."""
        async with self._lock:
            if model.model_id in self._loaded_models:
                model.lifecycle_state = ModelLifecycleState.LOADED
                return model

            logger.info(
                "Loading development model: '%s' (%s)", model.model_id, model.target_runtime
            )
            try:
                model.transition_to(ModelLifecycleState.LOADING)
                # Brief async boundary simulating load preparation
                await asyncio.sleep(0.01)
                model.transition_to(ModelLifecycleState.LOADED)
                self._loaded_models.add(model.model_id)
                logger.info("Development model loaded successfully: '%s'", model.model_id)
                return model
            except Exception as exc:
                logger.error("Failed loading model '%s': %s", model.model_id, exc)
                model.lifecycle_state = ModelLifecycleState.FAILED
                raise ModelLoadError(
                    f"Failed to load model '{model.model_id}': {exc!s}",
                    details={"model_id": model.model_id},
                ) from exc

    async def unload(self, model: Model) -> Model:
        """Unload development stub model from active state."""
        async with self._lock:
            if (
                model.model_id not in self._loaded_models
                and model.lifecycle_state != ModelLifecycleState.LOADED
            ):
                model.lifecycle_state = ModelLifecycleState.AVAILABLE
                return model

            logger.info("Unloading development model: '%s'", model.model_id)
            try:
                model.transition_to(ModelLifecycleState.UNLOADING)
                await asyncio.sleep(0.01)
                model.transition_to(ModelLifecycleState.AVAILABLE)
                self._loaded_models.discard(model.model_id)
                logger.info("Development model unloaded successfully: '%s'", model.model_id)
                return model
            except Exception as exc:
                logger.error("Failed unloading model '%s': %s", model.model_id, exc)
                model.lifecycle_state = ModelLifecycleState.FAILED
                raise ModelUnloadError(
                    f"Failed to unload model '{model.model_id}': {exc!s}",
                    details={"model_id": model.model_id},
                ) from exc

    async def is_loaded(self, model: Model) -> bool:
        """Check if model is currently marked loaded."""
        async with self._lock:
            return model.model_id in self._loaded_models
