from __future__ import annotations
"""Plain text file reader."""

import logging
from pathlib import Path

from app.schemas.tools import ToolResult
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

TOOL_NAME = "text_reader"


def read_text_file(file_path: str) -> str:
    """Read UTF-8 text from a file.

    Args:
        file_path: Path to a text file.

    Returns:
        File contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If reading fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")
    try:
        return path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"File is not valid UTF-8 text: {file_path}") from exc


class TextReaderTool(BaseTool):
    """Read plain text files."""

    name = TOOL_NAME
    description = "Read content from plain text files."

    def run(self, **kwargs: object) -> ToolResult:
        """Read text from ``file_path``."""
        file_path = kwargs.get("file_path")
        if not file_path or not isinstance(file_path, str):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: file_path",
            )

        logger.info("Reading text file: path=%s", file_path)
        try:
            content = read_text_file(file_path)
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"file_path": file_path, "char_count": len(content)},
                output_text=content,
            )
        except (FileNotFoundError, RuntimeError) as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                data={"file_path": file_path},
            )
