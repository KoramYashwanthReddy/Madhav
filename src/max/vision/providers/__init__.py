"""Providers package for Module 25 — Vision System."""

from max.vision.providers.base import VisionProvider
from max.vision.providers.mock_provider import MockVisionProvider

__all__ = ["MockVisionProvider", "VisionProvider"]
