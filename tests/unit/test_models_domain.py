"""Unit tests for Module 05 Model Management domain layer entities."""

from pathlib import Path

import pytest

from max.models.domain.artifact import ModelLocation
from max.models.domain.capabilities import ModelCapabilities
from max.models.domain.enums import ModelLifecycleState, ModelProvider
from max.models.domain.identity import ModelIdentifier
from max.models.domain.model import Model
from max.models.domain.requirements import HardwareProfile, ModelRequirements


class TestModelDomainEntities:
    """Unit tests for domain entities and value objects."""

    def test_model_identifier(self) -> None:
        ident = ModelIdentifier(
            model_id="test-model-1",
            provider=ModelProvider.LOCAL,
            name="Test Model",
            version="1.0.0",
        )
        assert ident.model_id == "test-model-1"
        assert ident.provider == ModelProvider.LOCAL
        assert ident.canonical_id == "test-model-1"

    def test_model_capabilities_defaults(self) -> None:
        caps = ModelCapabilities()
        assert caps.text_generation is True
        assert caps.chat is True
        assert caps.vision is False

    def test_model_requirements(self) -> None:
        reqs = ModelRequirements(minimum_ram_gb=4.0, context_length=8192)
        assert reqs.minimum_ram_gb == 4.0
        assert reqs.context_length == 8192

    def test_hardware_profile_detection(self) -> None:
        profile = HardwareProfile.detect()
        assert profile.operating_system != ""
        assert profile.cpu_count >= 1
        assert profile.system_memory_gb > 0.0

    def test_model_lifecycle_state_transitions(self) -> None:
        model = Model(
            identifier=ModelIdentifier(
                model_id="stub-1",
                provider=ModelProvider.DEVELOPMENT,
                name="Stub 1",
            ),
            lifecycle_state=ModelLifecycleState.REGISTERED,
        )
        assert model.is_available is False
        assert model.is_loaded is False

        model.transition_to(ModelLifecycleState.AVAILABLE)
        assert model.is_available is True

        model.transition_to(ModelLifecycleState.LOADING)
        model.transition_to(ModelLifecycleState.LOADED)
        assert model.is_loaded is True

        model.transition_to(ModelLifecycleState.UNLOADING)
        model.transition_to(ModelLifecycleState.AVAILABLE)
        assert model.is_loaded is False

    def test_invalid_lifecycle_transition_raises_error(self) -> None:
        model = Model(
            identifier=ModelIdentifier(
                model_id="stub-2",
                provider=ModelProvider.DEVELOPMENT,
                name="Stub 2",
            ),
            lifecycle_state=ModelLifecycleState.REGISTERED,
        )
        with pytest.raises(ValueError, match="Invalid lifecycle transition"):
            model.transition_to(ModelLifecycleState.LOADED)


class TestModelLocationSecurity:
    """Unit tests for ModelLocation safe path handling and checksums."""

    def test_resolve_safe_path_valid(self, tmp_path: Path) -> None:
        resolver = ModelLocation(tmp_path)
        sub_file = tmp_path / "sub" / "model.bin"
        resolved = resolver.resolve_safe_path("sub/model.bin")
        assert resolved == sub_file.resolve()

    def test_resolve_safe_path_traversal_attack_raises_error(self, tmp_path: Path) -> None:
        resolver = ModelLocation(tmp_path)
        with pytest.raises(ValueError, match="Path traversal detected"):
            resolver.resolve_safe_path("../../../etc/passwd")

    def test_verify_checksum(self, tmp_path: Path) -> None:
        resolver = ModelLocation(tmp_path)
        test_file = tmp_path / "artifact.txt"
        test_file.write_text("max-test-content", encoding="utf-8")

        import hashlib

        expected_sha = hashlib.sha256(b"max-test-content").hexdigest()

        assert resolver.verify_checksum("artifact.txt", expected_sha) is True
        assert resolver.verify_checksum("artifact.txt", "wrong_hash") is False
