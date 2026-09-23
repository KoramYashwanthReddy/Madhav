"""Core ModelManager facade orchestrating model lifecycle, discovery, and runtime compatibility."""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from max.ai.domain.capabilities import RuntimeCapabilities
from max.config.settings import get_settings
from max.models.domain.artifact import ModelArtifact, ModelLocation
from max.models.domain.capabilities import ModelCapabilities
from max.models.domain.enums import ModelFormat, ModelLifecycleState, ModelProvider
from max.models.domain.identity import ModelIdentifier
from max.models.domain.model import Model
from max.models.domain.requirements import ModelRequirements
from max.models.domain.status import ModelStatus
from max.models.exceptions import (
    ModelAlreadyExistsError,
    ModelCompatibilityError,
    ModelIntegrityError,
    ModelValidationError,
)
from max.models.services.loaders import DevelopmentModelLoader, ModelLoader
from max.models.services.registry import ModelRegistry
from max.models.services.repositories import InMemoryModelRepository, ModelRepository

logger = logging.getLogger("max.models.manager")


class ModelManager:
    """Facade orchestrating Model Management lifecycle, discovery, and runtime resolution."""

    def __init__(
        self,
        repository: ModelRepository | None = None,
        loader: ModelLoader | None = None,
        model_directory: Path | str | None = None,
    ) -> None:
        self._settings = get_settings()
        self._repository = repository or InMemoryModelRepository()
        self._registry = ModelRegistry(self._repository)
        self._loader = loader or DevelopmentModelLoader()

        model_dir = model_directory or self._settings.models.model_directory
        self._location_resolver = ModelLocation(model_dir)

        # Map maintaining per-model locks for concurrency protection
        self._model_locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

        # Initialize default development model
        self._initialize_default_development_model()

    @property
    def registry(self) -> ModelRegistry:
        """Expose inner model registry."""
        return self._registry

    @property
    def location_resolver(self) -> ModelLocation:
        """Expose model location resolver."""
        return self._location_resolver

    def _get_model_lock(self, model_id: str) -> asyncio.Lock:
        """Retrieve or create async lock for target model_id."""
        if model_id not in self._model_locks:
            self._model_locks[model_id] = asyncio.Lock()
        return self._model_locks[model_id]

    def _initialize_default_development_model(self) -> None:
        """Pre-register deterministic development stub model definition."""
        dev_model_id = "development-stub"
        dev_model = Model(
            identifier=ModelIdentifier(
                model_id=dev_model_id,
                provider=ModelProvider.DEVELOPMENT,
                name="Development Stub Model",
                version="1.0.0",
            ),
            capabilities=ModelCapabilities(
                text_generation=True,
                chat=True,
                streaming=True,
                vision=False,
                embeddings=False,
                tool_calling=False,
                structured_output=False,
                reasoning=False,
            ),
            requirements=ModelRequirements(
                minimum_ram_gb=0.1,
                recommended_ram_gb=0.5,
                cpu_required=True,
                gpu_required=False,
            ),
            artifact=ModelArtifact(
                model_id=dev_model_id,
                format=ModelFormat.UNKNOWN,
                path=None,
                status="available",
            ),
            target_runtime="stub",
            lifecycle_state=ModelLifecycleState.AVAILABLE,
            description="Deterministic development stub model operating completely offline.",
        )

        try:
            asyncio.run(self._registry.register_model(dev_model))
        except RuntimeError:
            # Event loop already running (e.g. inside async context),
            # insert directly into repository dict
            if hasattr(self._repository, "_models"):
                self._repository._models[dev_model.model_id] = dev_model

        except ModelAlreadyExistsError:
            pass

    async def register_model(self, model: Model) -> Model:
        """Register a new model definition with validation."""
        self._validate_model_definition(model)

        async with self._global_lock:
            # Set initial state to AVAILABLE if format is unknown or API/stub
            if model.identifier.provider in {
                ModelProvider.DEVELOPMENT,
                ModelProvider.OPENAI,
                ModelProvider.ANTHROPIC,
                ModelProvider.GOOGLE,
            }:
                model.lifecycle_state = ModelLifecycleState.AVAILABLE
            elif model.artifact and model.artifact.path:
                try:
                    resolved_path = self._location_resolver.resolve_safe_path(model.artifact.path)
                    if resolved_path.exists():
                        model.lifecycle_state = ModelLifecycleState.AVAILABLE
                    else:
                        model.lifecycle_state = ModelLifecycleState.UNAVAILABLE
                except ValueError as exc:
                    raise ModelValidationError(
                        f"Artifact path validation failed: {exc!s}",
                        details={"model_id": model.model_id, "path": model.artifact.path},
                    ) from exc
            else:
                model.lifecycle_state = ModelLifecycleState.REGISTERED

            return await self._registry.register_model(model)

    async def update_model(self, model_id: str, updates: dict[str, Any]) -> Model:
        """Update metadata for an existing model definition."""
        lock = self._get_model_lock(model_id)
        async with lock:
            existing = await self._registry.get_model(model_id)
            if existing.is_loaded:
                raise ModelValidationError(
                    f"Cannot update model '{model_id}' while in LOADED state. Unload model first.",
                    details={"model_id": model_id},
                )

            # Prevent mutating immutable identity fields
            if "model_id" in updates and updates["model_id"] != model_id:
                raise ModelValidationError("Cannot modify immutable model_id string.")

            if "description" in updates:
                existing.description = updates["description"]
            if "target_runtime" in updates:
                existing.target_runtime = updates["target_runtime"]
            if "metadata" in updates:
                existing.metadata.update(updates["metadata"])

            existing.updated_at = datetime.now(UTC)
            return await self._registry.update_model(existing)

    async def get_model(self, model_id: str) -> Model:
        """Retrieve model definition by model_id."""
        return await self._registry.get_model(model_id)

    async def list_models(
        self,
        provider: str | None = None,
        state: str | None = None,
        target_runtime: str | None = None,
    ) -> list[Model]:
        """List registered model definitions."""
        return await self._registry.list_models(
            provider=provider, state=state, target_runtime=target_runtime
        )

    async def delete_model(self, model_id: str) -> bool:
        """Unregister model definition (preserves on-disk files)."""
        lock = self._get_model_lock(model_id)
        async with lock:
            model = await self._registry.get_model(model_id)
            if model.is_loaded:
                await self._loader.unload(model)

            return await self._registry.unregister_model(model_id)

    async def load_model(self, model_id: str) -> Model:
        """Load model into operational state with concurrency protection."""
        lock = self._get_model_lock(model_id)
        async with lock:
            model = await self._registry.get_model(model_id)
            if model.is_loaded:
                logger.info("Model '%s' is already LOADED.", model_id)
                return model

            if model.lifecycle_state == ModelLifecycleState.UNAVAILABLE:
                raise ModelValidationError(
                    f"Cannot load model '{model_id}': Model artifact is UNAVAILABLE.",
                    details={"model_id": model_id},
                )

            loaded_model = await self._loader.load(model)
            await self._registry.update_model(loaded_model)
            return loaded_model

    async def unload_model(self, model_id: str) -> Model:
        """Unload model from operational state with concurrency protection."""
        lock = self._get_model_lock(model_id)
        async with lock:
            model = await self._registry.get_model(model_id)
            if not model.is_loaded and model.lifecycle_state == ModelLifecycleState.AVAILABLE:
                logger.info("Model '%s' is already UNLOADED.", model_id)
                return model

            unloaded_model = await self._loader.unload(model)
            await self._registry.update_model(unloaded_model)
            return unloaded_model

    async def get_status(self, model_id: str) -> ModelStatus:
        """Return diagnostic status snapshot for model."""
        model = await self._registry.get_model(model_id)
        is_loaded = await self._loader.is_loaded(model)

        artifact_path_str = None
        if model.artifact and model.artifact.path:
            artifact_path_str = str(model.artifact.path)

        return ModelStatus(
            model_id=model.model_id,
            provider=model.identifier.provider,
            lifecycle_state=model.lifecycle_state,
            is_available=model.is_available,
            is_loaded=is_loaded,
            target_runtime=model.target_runtime,
            capabilities=model.capabilities,
            format=model.artifact.format if model.artifact else ModelFormat.UNKNOWN,
            artifact_path=artifact_path_str,
            error_message=None,
        )

    async def verify_artifact_checksum(self, model_id: str) -> bool:
        """Verify checksum integrity for local model artifact."""
        model = await self._registry.get_model(model_id)
        if not model.artifact or not model.artifact.path or not model.artifact.checksum:
            raise ModelIntegrityError(
                f"Model '{model_id}' does not specify a checksum or artifact path.",
                details={"model_id": model_id},
            )

        try:
            valid = self._location_resolver.verify_checksum(
                file_path=model.artifact.path,
                expected_checksum=model.artifact.checksum,
                algorithm=model.artifact.checksum_algorithm,
            )
            if not valid:
                model.transition_to(ModelLifecycleState.FAILED)
                await self._registry.update_model(model)
                raise ModelIntegrityError(
                    f"Checksum verification failed for model '{model_id}'.",
                    details={"model_id": model_id},
                )
            return True
        except ValueError as exc:
            raise ModelValidationError(
                f"Path traversal or file error during verification: {exc!s}",
                details={"model_id": model_id},
            ) from exc

    def validate_compatibility(
        self, model: Model, runtime_capabilities: RuntimeCapabilities
    ) -> bool:
        """Check if model capabilities are compatible with target runtime capabilities."""
        if model.capabilities.vision and not runtime_capabilities.vision:
            raise ModelCompatibilityError(
                f"Model '{model.model_id}' requires vision capability, "
                "but target runtime does not support it.",
                details={"model_id": model.model_id},
            )
        if model.capabilities.streaming and not runtime_capabilities.streaming:
            raise ModelCompatibilityError(
                f"Model '{model.model_id}' requires streaming capability, "
                "but target runtime does not support it.",
                details={"model_id": model.model_id},
            )
        return True

    async def discover_local_models(self) -> list[Model]:
        """Scan configured local model directory for candidate model files."""
        discovered: list[Model] = []
        root = self._location_resolver.root_directory
        if not root.exists() or not root.is_dir():
            logger.info("Model directory '%s' does not exist. Skipping auto-discovery.", root)
            return discovered

        supported_extensions = {
            ".gguf": ModelFormat.GGUF,
            ".safetensors": ModelFormat.SAFETENSORS,
            ".onnx": ModelFormat.ONNX,
        }

        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in supported_extensions:
                fmt = supported_extensions[path.suffix.lower()]
                rel_path = path.relative_to(root)
                candidate_id = f"local-{path.stem.lower().replace(' ', '-')}"

                if not await self._repository.exists(candidate_id):
                    model = Model(
                        identifier=ModelIdentifier(
                            model_id=candidate_id,
                            provider=ModelProvider.LOCAL,
                            name=path.stem,
                            version="1.0.0",
                        ),
                        capabilities=ModelCapabilities(text_generation=True, chat=True),
                        artifact=ModelArtifact(
                            model_id=candidate_id,
                            format=fmt,
                            path=str(rel_path),
                            size_bytes=path.stat().st_size,
                            status="available",
                        ),
                        target_runtime="local",
                        lifecycle_state=ModelLifecycleState.AVAILABLE,
                        description=f"Discovered local model file: {rel_path}",
                    )
                    registered = await self._registry.register_model(model)
                    discovered.append(registered)

        return discovered

    def _validate_model_definition(self, model: Model) -> None:
        """Validate model entity constraints."""
        if not model.model_id or not model.model_id.strip():
            raise ModelValidationError("model_id cannot be empty.")
        if not model.identifier.name or not model.identifier.name.strip():
            raise ModelValidationError("Model name cannot be empty.")
