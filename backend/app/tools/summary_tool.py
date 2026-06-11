"""Text summarization via Groq LLM."""

from __future__ import annotations

import logging
from typing import Optional

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.core.llm import groq_chat_completion_with_usage
from app.schemas.cost import CostEstimate, TokenUsage
from app.schemas.tools import ToolResult
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

TOOL_NAME = "summarizer"
_MAX_INPUT_CHARS = 50_000

_SYSTEM_PROMPT = (
    "You are a concise summarization assistant. "
    "Produce a clear, well-structured summary of the provided content. "
    "Use bullet points when appropriate. Output plain text only."
)


class SummarizerTool(BaseTool):
    """Summarize text content using an LLM."""

    name = TOOL_NAME
    description = "Summarize text content into a concise plain-text response."

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    def run(self, **kwargs: object) -> ToolResult:
        """Summarize the provided ``text``.

        Args:
            **kwargs: Expected key ``text`` (str).

        Returns:
            ToolResult with summary in ``output_text``.
        """
        text = kwargs.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing or empty required parameter: text",
            )

        truncated = text.strip()[:_MAX_INPUT_CHARS]
        logger.info("Summarizing text: input_chars=%d", len(truncated))

        try:
            summary, usage = groq_chat_completion_with_usage(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=truncated,
                model=self._settings.groq_model,
            )

            # Calculate cost estimate
            usage_obj = TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )
            cost_estimate = CostEstimate.from_usage(
                tool_name=self.name,
                model=self._settings.groq_model,
                usage=usage_obj,
            )

            logger.info("Summarization complete: output_chars=%d", len(summary))
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"input_chars": len(truncated), "output_chars": len(summary)},
                output_text=summary,
                cost_estimate=cost_estimate,
            )
        except ConfigurationError as exc:
            logger.error("Summarizer configuration error: %s", exc.message)
            return ToolResult(tool_name=self.name, success=False, error=exc.message)
        except RuntimeError as exc:
            logger.error("Summarization failed: %s", exc)
            return ToolResult(tool_name=self.name, success=False, error=str(exc))
        except Exception as exc:
            logger.exception("Unexpected summarization error")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Unexpected error during summarization: {exc}",
            )
