"""Tool integration for Module 26 — Speech System.

Registers controlled speech tools with Module 14 ToolRegistry.
"""

from __future__ import annotations

import logging
from typing import Any

from max.tools.domain.enums import ToolCapability, ToolCategory, ToolRiskLevel, ToolSource
from max.tools.services.registry import ToolRegistryService

logger = logging.getLogger(__name__)

SPEECH_TOOLS = [
    {
        "name": "speech.transcribe",
        "description": "Transcribe spoken audio bytes into structured text with timestamps.",
        "category": ToolCategory.MEDIA,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "speech.synthesize",
        "description": "Convert input text into spoken audio WAV stream.",
        "category": ToolCategory.MEDIA,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "speech.detect_activity",
        "description": "Analyze audio data to detect active speech or silence.",
        "category": ToolCategory.MEDIA,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "speech.list_voices",
        "description": "List available text-to-speech voice models and attributes.",
        "category": ToolCategory.MEDIA,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
    {
        "name": "speech.list_devices",
        "description": "Enumerate available system microphone and speaker hardware devices.",
        "category": ToolCategory.MEDIA,
        "risk_level": ToolRiskLevel.LOW,
        "capabilities": [ToolCapability.TEXT_TRANSFORMATION],
    },
]


def register_speech_tools(tool_registry: ToolRegistryService) -> list[str]:
    """Register all Module 26 Speech tools with the ToolRegistry."""
    registered_ids: list[str] = []

    for tool_def in SPEECH_TOOLS:
        name_str: str = str(tool_def["name"])
        desc_str: str = str(tool_def["description"])
        caps: list[ToolCapability] = tool_def["capabilities"]  # type: ignore[assignment]
        risk: ToolRiskLevel = tool_def["risk_level"]  # type: ignore[assignment]
        cat: ToolCategory = tool_def["category"]  # type: ignore[assignment]

        try:
            existing, _ = tool_registry.list_tools(search_query=name_str)
            if any(t.name == name_str for t in existing):
                continue

            tool = tool_registry.register_tool(
                name=name_str,
                description=desc_str,
                version="1.0.0",
                category=cat,
                capabilities=caps,
                risk_level=risk,
                source=ToolSource.BUILT_IN,
                owner_id="system",
            )
            tool_registry.activate_tool(tool.id)
            registered_ids.append(tool.id)
        except Exception as exc:
            logger.debug("Tool '%s' registration failed or skipped: %s", name_str, exc)

    logger.info("Registered %d speech tools in ToolRegistry.", len(registered_ids))
    return registered_ids
