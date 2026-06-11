"""Tool registry unit tests."""

from pathlib import Path

import pytest

from app.core.exceptions import ToolExecutionError
from app.tools.bootstrap import create_tool_registry
from app.tools.registry import ToolRegistry


def test_registry_run_unknown_tool() -> None:
    """Unknown tool name raises ToolExecutionError."""
    registry = ToolRegistry()
    with pytest.raises(ToolExecutionError, match="Unknown tool"):
        registry.run("nonexistent_tool")


def test_registry_lists_all_tools() -> None:
    """Default registry exposes all implemented tools."""
    registry = create_tool_registry()
    tools = registry.list_tools()
    assert "pdf_extractor" in tools
    assert "image_ocr" in tools
    assert "audio_transcriber" in tools
    assert "youtube_transcript" in tools
    assert "summarizer" in tools
    assert "sentiment_analyzer" in tools
    assert "code_analyzer" in tools


def test_registry_executes_pdf_extractor(sample_pdf_path: Path) -> None:
    """Registry dispatches to pdf_extractor successfully."""
    registry = create_tool_registry()
    result = registry.run("pdf_extractor", file_path=str(sample_pdf_path))

    assert result.success is True
    assert result.output_text is not None
