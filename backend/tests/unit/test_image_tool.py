"""Image OCR tool unit tests."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from pytesseract import TesseractError

from app.tools.image_tool import ImageOcrTool, extract_image_text


def test_extract_image_text_file_not_found() -> None:
    """Missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extract_image_text("/nonexistent/image.png")


def test_image_ocr_tool_tesseract_error(tmp_path: Path) -> None:
    """TesseractError is converted to a clear RuntimeError."""
    image_path = tmp_path / "test.png"
    Image.new("RGB", (10, 10), color="white").save(image_path)

    with patch("app.tools.image_tool.pytesseract.image_to_string") as mock_ocr:
        mock_ocr.side_effect = TesseractError(1, "OCR failed")
        with pytest.raises(RuntimeError, match="Tesseract OCR processing failed"):
            extract_image_text(str(image_path))


def test_image_ocr_tool_missing_parameter() -> None:
    """Tool returns failure when file_path is missing."""
    tool = ImageOcrTool()
    result = tool.run()
    assert result.success is False
    assert "file_path" in (result.error or "")
