"""Abstract vision provider interface for Module 25 — Vision System.

All concrete providers (local models, remote APIs, mock) must implement
VisionProvider. Higher-level modules interact only with this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from max.vision.domain.enums import VisionCapability, VisionInputType
from max.vision.domain.models import (
    VisionAnalysisResult,
    VisionChart,
    VisionClassification,
    VisionDescription,
    VisionDiagram,
    VisionImage,
    VisionModel,
    VisionModelConfiguration,
    VisionObjectDetection,
    VisionOCRResult,
    VisionRequest,
    VisionUIAnalysis,
)


class VisionProvider(ABC):
    """Provider-neutral abstract interface for vision analysis.

    Concrete implementations must:
    - Not expose provider-specific data structures to callers
    - Normalize all results into Max canonical models
    - Handle their own model lifecycle (load/unload)
    - Never perform actions (no keyboard, mouse, browser interaction)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier (e.g. 'mock', 'local-transformers', 'gemini')."""

    @property
    @abstractmethod
    def supported_capabilities(self) -> list[VisionCapability]:
        """List of capabilities this provider can fulfill."""

    @abstractmethod
    def supported_models(self) -> list[VisionModel]:
        """List all models this provider makes available."""

    @abstractmethod
    def supports_input(self, input_type: VisionInputType) -> bool:
        """Return True if this provider can process the given input type."""

    @abstractmethod
    def supports_capability(self, capability: VisionCapability) -> bool:
        """Return True if this provider supports the given capability."""

    @abstractmethod
    async def analyze(
        self,
        image: VisionImage,
        data: bytes,
        request: VisionRequest,
        model_config: VisionModelConfiguration,
    ) -> VisionAnalysisResult:
        """Full analysis pipeline — routes to specific capability methods."""

    @abstractmethod
    async def ocr(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionOCRResult:
        """Extract text via OCR from an image."""

    @abstractmethod
    async def detect_objects(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionObjectDetection:
        """Detect and locate objects in an image."""

    @abstractmethod
    async def classify(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> list[VisionClassification]:
        """Classify the content of an image."""

    @abstractmethod
    async def describe(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionDescription:
        """Generate a structured natural-language description of an image."""

    @abstractmethod
    async def analyze_ui(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionUIAnalysis:
        """Detect and classify UI elements in a screenshot."""

    @abstractmethod
    async def analyze_document_image(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionOCRResult:
        """Analyze a document page image, returning OCR with document structure hints."""

    @abstractmethod
    async def analyze_chart(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> list[VisionChart]:
        """Detect and extract chart observations from an image."""

    @abstractmethod
    async def analyze_diagram(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> list[VisionDiagram]:
        """Detect and extract diagram observations from an image."""
