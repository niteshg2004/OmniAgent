from __future__ import annotations
from typing import Optional, Union
"""Code extraction and analysis."""

import logging
import re

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.core.llm import groq_chat_completion
from app.schemas.tools import ToolResult
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

TOOL_NAME = "code_analyzer"
_MAX_INPUT_CHARS = 50_000

_CODE_BLOCK_PATTERN = re.compile(r"```[\w]*\n(.*?)```", re.DOTALL)

_SYSTEM_PROMPT = (
    "You are a code analysis assistant. Review the provided code or technical content. "
    "Explain what it does, identify languages used, note potential issues, "
    "and suggest improvements. Output plain text only."
)


def extract_code_blocks(text: str) -> list[str]:
    """Extract fenced code blocks from markdown-style text.

    Args:
        text: Raw text that may contain ``` code fences.

    Returns:
        List of code block contents; empty if none found.
    """
    return [match.group(1).strip() for match in _CODE_BLOCK_PATTERN.finditer(text)]


class CodeAnalyzerTool(BaseTool):
    """Extract and analyze code from text."""

    name = TOOL_NAME
    description = "Analyze code blocks and explain their behavior."

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    def run(self, **kwargs: object) -> ToolResult:
        """Analyze code in ``text``.

        Args:
            **kwargs: Expected key ``text`` (str).

        Returns:
            ToolResult with analysis in ``output_text``.
        """
        text = kwargs.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing or empty required parameter: text",
            )

        content = text.strip()[:_MAX_INPUT_CHARS]
        code_blocks = extract_code_blocks(content)
        analysis_input = (
            "\n\n---\n\n".join(code_blocks) if code_blocks else content
        )

        logger.info(
            "Analyzing code: blocks=%d input_chars=%d",
            len(code_blocks),
            len(analysis_input),
        )

        try:
            analysis = groq_chat_completion(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=analysis_input,
                model=self._settings.groq_model,
            )
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "code_blocks_found": len(code_blocks),
                    "input_chars": len(analysis_input),
                },
                output_text=analysis,
            )
        except ConfigurationError as exc:
            return ToolResult(tool_name=self.name, success=False, error=exc.message)
        except RuntimeError as exc:
            return ToolResult(tool_name=self.name, success=False, error=str(exc))
        except Exception as exc:
            logger.exception("Unexpected code analysis error")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Unexpected error during code analysis: {exc}",
            )
