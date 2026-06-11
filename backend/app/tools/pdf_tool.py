from __future__ import annotations
"""PDF text extraction using PyMuPDF (fitz)."""

import logging
from pathlib import Path

import fitz

from app.schemas.tools import ToolResult
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

TOOL_NAME = "pdf_extractor"


def extract_pdf_text(file_path: str) -> tuple[str, int]:
    """Extract text from all pages of a PDF file.

    Args:
        file_path: Absolute or relative path to a PDF file.

    Returns:
        Tuple of (combined page text, page count).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file or the PDF has no pages.
        RuntimeError: If PDF parsing fails.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        with fitz.open(path) as document:
            page_count = document.page_count
            if page_count == 0:
                raise ValueError(f"PDF has no pages: {file_path}")

            page_texts: list[str] = []
            for page_index in range(page_count):
                page = document[page_index]
                text = page.get_text().strip()
                if text:
                    page_texts.append(f"--- Page {page_index + 1} ---\n{text}")

            combined_text = "\n\n".join(page_texts)
            return combined_text, page_count

    except fitz.FileDataError as exc:
        raise RuntimeError(f"Invalid or corrupted PDF file: {file_path}") from exc
    except fitz.FileError as exc:
        raise RuntimeError(f"Failed to open PDF file: {file_path}") from exc


class PdfExtractorTool(BaseTool):
    """Extract plain text from PDF documents."""

    name = TOOL_NAME
    description = "Extract text content from all pages of a PDF file."

    def run(self, **kwargs: object) -> ToolResult:
        """Extract text from a PDF at the given path.

        Args:
            **kwargs: Expected key ``file_path`` (str).

        Returns:
            ToolResult with extracted text in ``output_text`` and page metadata in ``data``.
        """
        file_path = kwargs.get("file_path")
        if not file_path or not isinstance(file_path, str):
            logger.error("pdf_extractor called without valid file_path")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: file_path",
            )

        logger.info("Extracting PDF text: path=%s", file_path)

        try:
            text, page_count = extract_pdf_text(file_path)
            char_count = len(text)

            if char_count == 0:
                logger.warning(
                    "PDF extraction returned no text (likely scanned/image PDF): path=%s",
                    file_path,
                )

            logger.info(
                "PDF extraction complete: path=%s pages=%d chars=%d",
                file_path,
                page_count,
                char_count,
            )

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "file_path": file_path,
                    "page_count": page_count,
                    "char_count": char_count,
                    "has_text": char_count > 0,
                },
                output_text=text,
            )

        except FileNotFoundError as exc:
            logger.error("PDF not found: %s", exc)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                data={"file_path": file_path},
            )
        except ValueError as exc:
            logger.error("PDF validation failed: %s", exc)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                data={"file_path": file_path},
            )
        except RuntimeError as exc:
            logger.error("PDF extraction failed: %s", exc)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                data={"file_path": file_path},
            )
        except Exception as exc:
            logger.exception("Unexpected PDF extraction error: path=%s", file_path)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Unexpected error during PDF extraction: {exc}",
                data={"file_path": file_path},
            )
