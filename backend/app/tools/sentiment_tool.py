"""Sentiment analysis via Groq LLM."""

from __future__ import annotations

import logging
from typing import Optional

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.core.llm import groq_chat_completion
from app.schemas.tools import ToolResult
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

TOOL_NAME = "sentiment_analyzer"
_MAX_INPUT_CHARS = 50_000

_SYSTEM_PROMPT = (
    "You are a sentiment analysis assistant. Analyze the emotional tone of the text. "
    "Respond in plain text with: overall sentiment (positive/negative/neutral/mixed), "
    "confidence level, key emotional indicators, and a brief explanation."
)


class SentimentAnalyzerTool(BaseTool):
    """Analyze sentiment of text content."""

    name = TOOL_NAME
    description = "Analyze the sentiment and emotional tone of text."

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    def run(self, **kwargs: object) -> ToolResult:
        """Analyze sentiment of ``text``.

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

        truncated = text.strip()[:_MAX_INPUT_CHARS]
        logger.info("Analyzing sentiment: input_chars=%d", len(truncated))

        try:
            analysis = groq_chat_completion(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=truncated,
                model=self._settings.groq_model,
            )
            logger.info("Sentiment analysis complete")
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"input_chars": len(truncated)},
                output_text=analysis,
            )
        except ConfigurationError as exc:
            return ToolResult(tool_name=self.name, success=False, error=exc.message)
        except RuntimeError as exc:
            return ToolResult(tool_name=self.name, success=False, error=str(exc))
        except Exception as exc:
            logger.exception("Unexpected sentiment analysis error")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Unexpected error during sentiment analysis: {exc}",
            )
