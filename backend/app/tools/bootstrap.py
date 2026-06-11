from __future__ import annotations
from typing import Optional, Union
"""Tool registry bootstrap — registers all available tools."""

import logging

from app.core.config import Settings, get_settings
from app.tools.audio_tool import AudioTranscriberTool
from app.tools.code_tool import CodeAnalyzerTool
from app.tools.image_tool import ImageOcrTool
from app.tools.pdf_tool import PdfExtractorTool
from app.tools.registry import ToolRegistry
from app.tools.sentiment_tool import SentimentAnalyzerTool
from app.tools.summary_tool import SummarizerTool
from app.tools.text_tool import TextReaderTool
from app.tools.youtube_tool import YoutubeTranscriptTool

logger = logging.getLogger(__name__)


def create_tool_registry(settings: Optional[Settings] = None) -> ToolRegistry:
    """Create a registry with all default OmniAgent tools registered.

    Args:
        settings: Optional settings override (useful in tests).

    Returns:
        Configured ToolRegistry ready for planner execution.
    """
    cfg = settings or get_settings()
    registry = ToolRegistry()

    registry.register(PdfExtractorTool())
    registry.register(ImageOcrTool())
    registry.register(TextReaderTool())
    registry.register(AudioTranscriberTool(cfg))
    registry.register(YoutubeTranscriptTool())
    registry.register(SummarizerTool(cfg))
    registry.register(SentimentAnalyzerTool(cfg))
    registry.register(CodeAnalyzerTool(cfg))

    logger.debug("Tool registry initialized with tools: %s", registry.list_tools())
    return registry
