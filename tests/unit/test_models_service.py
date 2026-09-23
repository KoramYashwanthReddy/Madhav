"""Unit tests for Module 05 Model Management service layer."""

import asyncio
from pathlib import Path

import pytest

from max.models.domain.artifact import ModelArtifact
from max.models.domain.enums import ModelFormat, ModelLifecycleState, ModelProvider
from max.models.domain.identity import ModelIdentifier
from max.models.domain.model import Model
from max.models.exceptions import (
    ModelAlreadyExistsError,
)
from max.models.services.loaders import DevelopmentModelLoader
from max.models.services.manager import ModelManager
from max.models.services.repositories import InMemoryModelRepository


@pytest.fixture
def repo() -> InMemoryModelRepository:
    return InMemoryModelRepository()


@pytest.fixture
def loader() -> DevelopmentModelLoader:
    return DevelopmentModelLoader()


@pytest.fixture
def manager(tmp_path: Path) -> ModelManager:
    repo = InMemoryModelRepository()
    loader = DevelopmentModelLoader()
    return ModelManager(repository=repo, loader=loader, model_directory=tmp_path)


class TestModelServices:
    """Unit tests for Model Management services."""

    @pytest.mark.asyncio
    async def test_repository_crud(self, repo: InMemoryModelRepository) -> None:
        model = Model(
            identifier=ModelIdentifier(model_id="m1", provider=ModelProvider.LOCAL, name="Model 1")
        )
        await repo.save(model)
        assert await repo.exists("m1") is True

        retrieved = await repo.get("m1")
        assert retrieved is not None
        assert retrieved.model_id == "m1"

        all_models = await repo.list_all()
        assert len(all_models) == 1

        assert await repo.delete("m1") is True
        assert await repo.exists("m1") is False

    @pytest.mark.asyncio
    async def test_loader_load_and_unload(self, loader: DevelopmentModelLoader) -> None:
        model = Model(
            identifier=ModelIdentifier(
                model_id="m2", provider=ModelProvider.DEVELOPMENT, name="Model 2"
            ),
            lifecycle_state=ModelLifecycleState.AVAILABLE,
        )

        loaded = await loader.load(model)
        assert loaded.lifecycle_state == ModelLifecycleState.LOADED
        assert await loader.is_loaded(model) is True

        unloaded = await loader.unload(loaded)
        assert unloaded.lifecycle_state == ModelLifecycleState.AVAILABLE
        assert await loader.is_loaded(model) is False

    @pytest.mark.asyncio
    async def test_manager_default_model_registration(self, manager: ModelManager) -> None:
        dev_model = await manager.get_model("development-stub")
        assert dev_model.model_id == "development-stub"
        assert dev_model.identifier.provider == ModelProvider.DEVELOPMENT
        assert dev_model.is_available is True

    @pytest.mark.asyncio
    async def test_manager_register_and_list_models(self, manager: ModelManager) -> None:
        new_model = Model(
            identifier=ModelIdentifier(
                model_id="custom-1", provider=ModelProvider.LOCAL, name="Custom Model"
            )
        )
        registered = await manager.register_model(new_model)
        assert registered.model_id == "custom-1"

        models = await manager.list_models()
        assert len(models) >= 2  # dev model + custom-1

    @pytest.mark.asyncio
    async def test_manager_duplicate_registration_raises_error(self, manager: ModelManager) -> None:
        with pytest.raises(ModelAlreadyExistsError):
            await manager.register_model(await manager.get_model("development-stub"))

    @pytest.mark.asyncio
    async def test_manager_load_and_unload_lifecycle(self, manager: ModelManager) -> None:
        model = await manager.get_model("development-stub")
        assert model.is_loaded is False

        loaded = await manager.load_model("development-stub")
        assert loaded.is_loaded is True

        unloaded = await manager.unload_model("development-stub")
        assert unloaded.is_loaded is False

    @pytest.mark.asyncio
    async def test_manager_concurrency_locking(self, manager: ModelManager) -> None:
        # Test concurrent load calls do not race
        results = await asyncio.gather(
            manager.load_model("development-stub"),
            manager.load_model("development-stub"),
        )
        assert results[0].is_loaded is True
        assert results[1].is_loaded is True

    @pytest.mark.asyncio
    async def test_manager_checksum_verification(
        self, manager: ModelManager, tmp_path: Path
    ) -> None:
        test_file = tmp_path / "model.gguf"
        test_file.write_text("model-data-payload", encoding="utf-8")

        import hashlib

        checksum = hashlib.sha256(b"model-data-payload").hexdigest()

        model = Model(
            identifier=ModelIdentifier(
                model_id="checksum-model", provider=ModelProvider.LOCAL, name="Checksum Model"
            ),
            artifact=ModelArtifact(
                model_id="checksum-model",
                format=ModelFormat.GGUF,
                path="model.gguf",
                checksum=checksum,
            ),
        )
        await manager.register_model(model)

        verified = await manager.verify_artifact_checksum("checksum-model")
        assert verified is True
