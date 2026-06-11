"""PDF extraction tool unit tests."""

from pathlib import Path

import pytest

from app.tools.bootstrap import create_tool_registry
from app.tools.pdf_tool import PdfExtractorTool, extract_pdf_text


def test_extract_pdf_text_returns_content(sample_pdf_path: Path) -> None:
    """Extracted text includes content from all pages."""
    text, page_count = extract_pdf_text(str(sample_pdf_path))

    assert page_count == 2
    assert "OmniAgent PDF test page one." in text
    assert "Second page content here." in text
    assert "--- Page 1 ---" in text
    assert "--- Page 2 ---" in text


def test_extract_pdf_text_file_not_found() -> None:
    """Missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found"):
        extract_pdf_text("/nonexistent/missing.pdf")


def test_extract_pdf_text_corrupt_file(corrupt_pdf_path: Path) -> None:
    """Corrupt PDF raises RuntimeError."""
    with pytest.raises(RuntimeError, match="Invalid or corrupted PDF"):
        extract_pdf_text(str(corrupt_pdf_path))


def test_extract_pdf_text_blank_page(blank_pdf_path: Path) -> None:
    """PDF with a blank page returns empty text but succeeds."""
    text, page_count = extract_pdf_text(str(blank_pdf_path))

    assert page_count == 1
    assert text == ""


def test_pdf_extractor_tool_blank_page_reports_no_text(blank_pdf_path: Path) -> None:
    """Tool marks has_text=False when extraction yields no content."""
    tool = PdfExtractorTool()
    result = tool.run(file_path=str(blank_pdf_path))

    assert result.success is True
    assert result.data["has_text"] is False
    assert result.data["char_count"] == 0
    assert result.output_text == ""


def test_pdf_extractor_tool_success(sample_pdf_path: Path) -> None:
    """Tool returns ToolResult with output_text on success."""
    tool = PdfExtractorTool()
    result = tool.run(file_path=str(sample_pdf_path))

    assert result.success is True
    assert result.tool_name == "pdf_extractor"
    assert result.error is None
    assert result.output_text is not None
    assert "OmniAgent PDF test page one." in result.output_text
    assert result.data["page_count"] == 2
    assert result.data["has_text"] is True


def test_pdf_extractor_tool_missing_file() -> None:
    """Tool returns failure result when file is missing."""
    tool = PdfExtractorTool()
    result = tool.run(file_path="/nonexistent/file.pdf")

    assert result.success is False
    assert result.error is not None
    assert "not found" in result.error.lower()


def test_pdf_extractor_tool_missing_parameter() -> None:
    """Tool returns failure when file_path is not provided."""
    tool = PdfExtractorTool()
    result = tool.run()

    assert result.success is False
    assert "file_path" in (result.error or "")


def test_pdf_extractor_registered_in_registry() -> None:
    """Default registry includes pdf_extractor."""
    registry = create_tool_registry()
    assert "pdf_extractor" in registry.list_tools()

    result = registry.run(
        "pdf_extractor",
        file_path=str(Path("/tmp/unused.pdf")),
    )
    assert result.success is False  # file does not exist; tool handled gracefully
