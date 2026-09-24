"""Mock Vision Provider for Module 25 — Vision System.

Provides deterministic, offline vision results for:
- Unit tests
- API tests
- Integration tests
- CI/CD environments
- Development without GPU/models

NEVER makes real AI calls. NEVER downloads models.
All results are hardcoded deterministic stubs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from max.vision.domain.enums import (
    VisionCapability,
    VisionChartType,
    VisionColorSpace,
    VisionConfidenceLevel,
    VisionInputType,
    VisionModelCapability,
    VisionModelStatus,
    VisionObjectClass,
    VisionObservationType,
    VisionProcessingStatus,
    VisionUIElementType,
)
from max.vision.domain.models import (
    VisionAnalysisResult,
    VisionBoundingBox,
    VisionChart,
    VisionCitation,
    VisionClassification,
    VisionConfidence,
    VisionDescription,
    VisionDiagram,
    VisionDiagramEdge,
    VisionDiagramNode,
    VisionImage,
    VisionModel,
    VisionModelConfiguration,
    VisionObservation,
    VisionOCRBlock,
    VisionOCRLine,
    VisionOCRResult,
    VisionOCRWord,
    VisionObject,
    VisionObjectDetection,
    VisionProcessingError,
    VisionProvenance,
    VisionRequest,
    VisionUIAnalysis,
    VisionUIElement,
)
from max.vision.providers.base import VisionProvider

_MOCK_MODEL_ID = "mock-vision-v1"
_MOCK_PROVIDER_NAME = "mock"


class MockVisionProvider(VisionProvider):
    """Deterministic mock vision provider.

    Returns hardcoded, reproducible results.
    Safe for all test environments.
    No GPU, no model downloads, no external calls.
    """

    @property
    def provider_name(self) -> str:
        return _MOCK_PROVIDER_NAME

    @property
    def supported_capabilities(self) -> list[VisionCapability]:
        return list(VisionCapability)

    def supported_models(self) -> list[VisionModel]:
        return [
            VisionModel(
                model_id=_MOCK_MODEL_ID,
                name="Mock Vision Model v1",
                version="1.0.0",
                provider=_MOCK_PROVIDER_NAME,
                capabilities=list(VisionModelCapability),
                status=VisionModelStatus.READY,
                max_image_size_mb=25.0,
                max_width=8192,
                max_height=8192,
            )
        ]

    def supports_input(self, input_type: VisionInputType) -> bool:
        return True  # Mock accepts all input types

    def supports_capability(self, capability: VisionCapability) -> bool:
        return True  # Mock supports all capabilities

    async def ocr(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionOCRResult:
        """Return a deterministic mock OCR result."""
        word = VisionOCRWord(
            text="MockOCRText",
            bounding_box=VisionBoundingBox(x=10, y=10, width=100, height=20),
            confidence=0.95,
        )
        line = VisionOCRLine(
            text="MockOCRText",
            bounding_box=VisionBoundingBox(x=10, y=10, width=100, height=20),
            confidence=0.95,
            words=[word],
            reading_order=0,
        )
        block = VisionOCRBlock(
            text="MockOCRText",
            bounding_box=VisionBoundingBox(x=10, y=10, width=200, height=40),
            confidence=0.95,
            lines=[line],
        )
        return VisionOCRResult(
            full_text="MockOCRText",
            blocks=[block],
            confidence=VisionConfidence(score=0.95, level=VisionConfidenceLevel.HIGH),
            language="en",
            is_untrusted_data=True,
        )

    async def detect_objects(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionObjectDetection:
        """Return a deterministic mock object detection result."""
        obj = VisionObject(
            object_class=VisionObjectClass.LAPTOP,
            label="laptop",
            confidence=VisionConfidence(score=0.92, level=VisionConfidenceLevel.HIGH),
            bounding_box=VisionBoundingBox(x=50, y=80, width=300, height=200),
            source_model=_MOCK_MODEL_ID,
        )
        return VisionObjectDetection(
            objects=[obj],
            total_detected=1,
            model_id=_MOCK_MODEL_ID,
        )

    async def classify(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> list[VisionClassification]:
        """Return a deterministic mock classification result."""
        return [
            VisionClassification(
                label="desktop_screenshot",
                confidence=VisionConfidence(score=0.88, level=VisionConfidenceLevel.HIGH),
                taxonomy="mock",
            ),
            VisionClassification(
                label="workspace",
                confidence=VisionConfidence(score=0.72, level=VisionConfidenceLevel.MEDIUM),
                taxonomy="mock",
            ),
        ]

    async def describe(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionDescription:
        """Return a deterministic mock image description."""
        return VisionDescription(
            summary="A mock image containing placeholder visual content for testing.",
            objects_mentioned=["laptop", "screen"],
            visible_text_summary="MockOCRText",
            scene_type="workspace",
            regions_described=["center: laptop", "background: desk"],
            uncertainties=["Color accuracy not verified in mock mode."],
            confidence=VisionConfidence(score=0.80, level=VisionConfidenceLevel.HIGH),
            is_untrusted_data=True,
        )

    async def analyze_ui(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionUIAnalysis:
        """Return a deterministic mock UI analysis result."""
        button = VisionUIElement(
            element_type=VisionUIElementType.BUTTON,
            visible_text="Submit",
            bounding_box=VisionBoundingBox(x=820, y=640, width=120, height=40),
            confidence=VisionConfidence(score=0.90, level=VisionConfidenceLevel.HIGH),
            interaction_role="submit",
            is_enabled=True,
        )
        input_field = VisionUIElement(
            element_type=VisionUIElementType.INPUT,
            visible_text="",
            bounding_box=VisionBoundingBox(x=100, y=200, width=400, height=36),
            confidence=VisionConfidence(score=0.85, level=VisionConfidenceLevel.HIGH),
            interaction_role="text_input",
            is_enabled=True,
        )
        return VisionUIAnalysis(
            elements=[button, input_field],
            layout_description="Mock UI: form with submit button and text input.",
            screenshot_context="browser",
        )

    async def analyze_document_image(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> VisionOCRResult:
        """Return a deterministic mock document OCR result."""
        return VisionOCRResult(
            full_text="Mock Document Title\n\nMock paragraph content for testing document vision.",
            blocks=[
                VisionOCRBlock(
                    text="Mock Document Title",
                    bounding_box=VisionBoundingBox(x=50, y=40, width=500, height=30),
                    confidence=0.97,
                ),
                VisionOCRBlock(
                    text="Mock paragraph content for testing document vision.",
                    bounding_box=VisionBoundingBox(x=50, y=100, width=500, height=60),
                    confidence=0.92,
                ),
            ],
            confidence=VisionConfidence(score=0.94, level=VisionConfidenceLevel.HIGH),
            language="en",
            is_untrusted_data=True,
        )

    async def analyze_chart(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> list[VisionChart]:
        """Return a deterministic mock chart analysis result."""
        return [
            VisionChart(
                chart_type=VisionChartType.BAR_CHART,
                title="Mock Chart",
                x_axis_label="Category",
                y_axis_label="Value",
                legend_labels=["Series A", "Series B"],
                visible_data_labels=["Q1", "Q2", "Q3", "Q4"],
                observed_trends=["Values appear to increase from Q1 to Q4."],
                bounding_box=VisionBoundingBox(x=20, y=20, width=600, height=400),
                confidence=VisionConfidence(score=0.78, level=VisionConfidenceLevel.MEDIUM),
                notes=["Exact numerical values not reliably extractable from mock provider."],
            )
        ]

    async def analyze_diagram(
        self,
        image: VisionImage,
        data: bytes,
        model_config: VisionModelConfiguration,
    ) -> list[VisionDiagram]:
        """Return a deterministic mock diagram analysis result."""
        node_a = VisionDiagramNode(label="User", node_type="actor")
        node_b = VisionDiagramNode(label="API", node_type="service")
        node_c = VisionDiagramNode(label="Database", node_type="store")
        edge_ab = VisionDiagramEdge(
            source_node_id=node_a.node_id,
            target_node_id=node_b.node_id,
            label="request",
            direction="→",
        )
        edge_bc = VisionDiagramEdge(
            source_node_id=node_b.node_id,
            target_node_id=node_c.node_id,
            label="query",
            direction="→",
        )
        return [
            VisionDiagram(
                diagram_type="architecture",
                nodes=[node_a, node_b, node_c],
                edges=[edge_ab, edge_bc],
                confidence=VisionConfidence(score=0.75, level=VisionConfidenceLevel.MEDIUM),
                notes=["Mock diagram — structural relationships are illustrative only."],
            )
        ]

    async def analyze(
        self,
        image: VisionImage,
        data: bytes,
        request: VisionRequest,
        model_config: VisionModelConfiguration,
    ) -> VisionAnalysisResult:
        """Full analysis routing — calls individual capability methods based on request."""
        from datetime import UTC, datetime

        result = VisionAnalysisResult(
            request_id=request.request_id,
            status=VisionProcessingStatus.ANALYZING,
            image=image,
        )

        provenance = VisionProvenance(
            vision_request_id=request.request_id,
            image_hash=image.metadata.content_hash,
            model_id=_MOCK_MODEL_ID,
            model_version="1.0.0",
            provider=_MOCK_PROVIDER_NAME,
        )

        caps = request.requested_capabilities

        if VisionCapability.OCR in caps:
            ocr = await self.ocr(image, data, model_config)
            result.ocr = ocr
            result.observations.append(
                VisionObservation(
                    observation_type=VisionObservationType.TEXT,
                    provenance=provenance,
                    confidence=ocr.confidence,
                    ocr_result=ocr,
                    raw_text=ocr.full_text,
                )
            )

        if VisionCapability.OBJECT_DETECTION in caps:
            det = await self.detect_objects(image, data, model_config)
            result.object_detection = det
            for obj in det.objects:
                result.observations.append(
                    VisionObservation(
                        observation_type=VisionObservationType.OBJECT,
                        provenance=provenance,
                        confidence=obj.confidence,
                        detected_object=obj,
                        bounding_box=obj.bounding_box,
                    )
                )

        if VisionCapability.IMAGE_CLASSIFICATION in caps:
            classifications = await self.classify(image, data, model_config)
            result.classifications = classifications

        if VisionCapability.IMAGE_DESCRIPTION in caps:
            desc = await self.describe(image, data, model_config)
            result.description = desc
            result.observations.append(
                VisionObservation(
                    observation_type=VisionObservationType.DESCRIPTION,
                    provenance=provenance,
                    confidence=desc.confidence,
                    description=desc,
                    raw_text=desc.summary,
                )
            )

        if VisionCapability.UI_ANALYSIS in caps:
            ui = await self.analyze_ui(image, data, model_config)
            result.ui_analysis = ui
            for elem in ui.elements:
                result.observations.append(
                    VisionObservation(
                        observation_type=VisionObservationType.UI_ELEMENT,
                        provenance=provenance,
                        confidence=elem.confidence,
                        ui_element=elem,
                        bounding_box=elem.bounding_box,
                    )
                )

        if VisionCapability.DOCUMENT_ANALYSIS in caps:
            doc_ocr = await self.analyze_document_image(image, data, model_config)
            result.ocr = doc_ocr  # Document analysis produces OCR

        if VisionCapability.CHART_ANALYSIS in caps:
            charts = await self.analyze_chart(image, data, model_config)
            result.charts = charts
            for chart in charts:
                result.observations.append(
                    VisionObservation(
                        observation_type=VisionObservationType.CHART,
                        provenance=provenance,
                        confidence=chart.confidence,
                        chart=chart,
                        bounding_box=chart.bounding_box,
                    )
                )

        if VisionCapability.DIAGRAM_ANALYSIS in caps:
            diagrams = await self.analyze_diagram(image, data, model_config)
            result.diagrams = diagrams
            for diag in diagrams:
                result.observations.append(
                    VisionObservation(
                        observation_type=VisionObservationType.DIAGRAM,
                        provenance=provenance,
                        confidence=diag.confidence,
                        diagram=diag,
                        bounding_box=diag.bounding_box,
                    )
                )

        result.citations = [
            VisionCitation(
                provenance=provenance,
                summary=f"Mock analysis of {image.image_id} via {_MOCK_PROVIDER_NAME}",
            )
        ]
        result.status = VisionProcessingStatus.COMPLETED
        result.completed_at = datetime.now(UTC)
        return result
