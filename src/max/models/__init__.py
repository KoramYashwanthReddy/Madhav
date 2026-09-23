"""MAX Model Management subsystem root package."""

from max.models.domain.model import Model
from max.models.services.manager import ModelManager

__all__ = ["Model", "ModelManager"]
