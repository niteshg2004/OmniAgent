from __future__ import annotations
"""Image OCR using Pillow and pytesseract."""

import logging
from pathlib import Path

import pytesseract
from PIL import Image
from pytesseract import TesseractError, TesseractNotFoundError

from app.schemas.tools import ToolResult
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

TOOL_NAME = "image_ocr"


def extract_image_text(file_path: str) -> tuple[str, float]:
    """Extract text from an image via OCR.

    Args:
        file_path: Path to an image file.

    Returns:
        Tuple of (extracted text, average confidence score).

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If OCR processing fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        with Image.open(path) as image:
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            extracted_text = pytesseract.image_to_string(image).strip()
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidence_data = data.get("confidence", [])
            confidences = [int(c) for c in confidence_data if int(c) > 0]
            average_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )
            return extracted_text, round(average_confidence, 2)

    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed. "
            "Install: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)"
        ) from exc
    except TesseractError as exc:
        raise RuntimeError(f"Tesseract OCR processing failed: {exc}") from exc
    except Image.UnidentifiedImageError as exc:
        raise RuntimeError(
            "Failed to identify image format. Ensure the file is a valid image."
        ) from exc


class ImageOcrTool(BaseTool):
    """Perform OCR on image files."""

    name = TOOL_NAME
    description = "Extract text from images using optical character recognition."

    def run(self, **kwargs: object) -> ToolResult:
        """Run OCR on the image at ``file_path``.

        Args:
            **kwargs: Expected key ``file_path`` (str).

        Returns:
            ToolResult with OCR text in ``output_text``.
        """
        file_path = kwargs.get("file_path")
        if not file_path or not isinstance(file_path, str):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: file_path",
            )

        logger.info("Running image OCR: path=%s", file_path)

        try:
            text, confidence = extract_image_text(file_path)
            logger.info(
                "Image OCR complete: path=%s chars=%d confidence=%.1f",
                file_path,
                len(text),
                confidence,
            )
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "file_path": file_path,
                    "char_count": len(text),
                    "confidence": confidence,
                    "has_text": len(text) > 0,
                },
                output_text=text,
            )
        except (FileNotFoundError, ValueError) as exc:
            logger.error("Image OCR validation failed: %s", exc)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                data={"file_path": file_path},
            )
        except RuntimeError as exc:
            logger.error("Image OCR failed: %s", exc)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                data={"file_path": file_path},
            )
        except Exception as exc:
            logger.exception("Unexpected image OCR error: path=%s", file_path)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Unexpected error during image OCR: {exc}",
                data={"file_path": file_path},
            )
