"""Global dependency injection container for Module 25 — Vision System."""

from max.config.settings import get_settings
from max.vision.preprocessing.preprocessor import ImagePreprocessor
from max.vision.preprocessing.validator import ImageValidator
from max.vision.providers.mock_provider import MockVisionProvider
from max.vision.security.enforcer import VisionSecurityEnforcer
from max.vision.services.vision_service import VisionCache, VisionService


class VisionContainer:
    """Dependency injection container for the Vision System subsystem."""

    def __init__(self) -> None:
        cfg = get_settings().vision
        self.settings = cfg

        # Infrastructure
        self.validator = ImageValidator(
            max_size_bytes=int(cfg.max_image_size_mb * 1024 * 1024),
            max_width=cfg.max_width,
            max_height=cfg.max_height,
            max_pixels=cfg.max_pixels,
            max_memory_mb=cfg.max_image_memory_mb,
        )
        self.preprocessor = ImagePreprocessor()
        self.security_enforcer = VisionSecurityEnforcer(
            camera_enabled=cfg.camera_enabled,
            screen_capture_enabled=cfg.screen_capture_enabled,
            privacy_redaction_enabled=cfg.privacy_redaction_enabled,
        )
        self.cache = VisionCache(
            max_entries=cfg.cache_max_entries,
            ttl_seconds=cfg.cache_ttl_seconds,
        )

        # Provider (mock by default; swap at integration time)
        self.provider = MockVisionProvider()

        # Master facade
        self.service = VisionService(
            provider=self.provider,
            validator=self.validator,
            preprocessor=self.preprocessor,
            security_enforcer=self.security_enforcer,
            cache=self.cache,
            cache_enabled=cfg.cache_enabled,
            default_model_id=cfg.default_model,
        )


_container_instance: VisionContainer | None = None


def get_vision_container() -> VisionContainer:
    """Retrieve or initialize the global VisionContainer instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = VisionContainer()
    return _container_instance


def reset_vision_container() -> None:
    """Reset the global VisionContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None
