from __future__ import annotations
from typing import Optional, Union
"""Concrete intent detection with rules and Groq LLM fallback."""

import json
import logging
import re

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.core.llm import groq_chat_completion
from app.planner.intent import IntentDetector, IntentResult, IntentType
from app.schemas.agent import AgentRequest
from app.utils.file_utils import FileType, detect_file_type
from app.utils.text_utils import extract_youtube_urls

logger = logging.getLogger(__name__)

_SUMMARIZE_PATTERN = re.compile(r"\b(summarize|summary|summarise|tldr|overview)\b", re.I)
_SENTIMENT_PATTERN = re.compile(r"\b(sentiment|tone|feeling|emotion)\b", re.I)
_TRANSCRIBE_PATTERN = re.compile(r"\b(transcribe|transcription|speech|audio)\b", re.I)
_EXTRACT_PATTERN = re.compile(r"\b(extract|read|ocr|text from)\b", re.I)
_CODE_PATTERN = re.compile(r"\b(code|function|script|program|debug)\b", re.I)
_YOUTUBE_PATTERN = re.compile(r"\b(youtube|video)\b", re.I)

_LLM_SYSTEM_PROMPT = """You classify user intent for a multimodal AI agent.
Return ONLY valid JSON with keys: intent, confidence, reasoning.
Valid intent values: summarize, sentiment_analysis, extract_text, transcribe,
youtube_summarize, code_analysis, custom, ambiguous.
Use ambiguous only when the user goal is truly unclear despite having a message.
confidence is a float between 0 and 1."""


class GroqIntentDetector(IntentDetector):
    """Detects intent using deterministic rules first, then Groq LLM."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    def detect(self, request: AgentRequest) -> IntentResult:
        """Analyze request and return intent or a follow-up question."""
        file_types = self._classify_files(request)
        message = (request.message or "").strip()

        rule_result = self._apply_rules(message, file_types, request)
        if rule_result:
            logger.info(
                "Intent resolved by rules: intent=%s confidence=%.2f",
                rule_result.intent.value,
                rule_result.confidence,
            )
            return rule_result

        if not message:
            return self._ambiguous_for_files(file_types)

        return self._detect_with_llm(message, file_types)

    def _classify_files(self, request: AgentRequest) -> list[FileType]:
        """Map uploaded files to file types."""
        types: list[FileType] = []
        for path, name in zip(request.file_paths, request.file_names):
            types.append(detect_file_type(name or path))
        return types

    def _apply_rules(
        self,
        message: str,
        file_types: list[FileType],
        request: AgentRequest,
    ) -> Optional[IntentResult]:
        """Apply deterministic intent rules; return None to defer to LLM."""
        if not message and file_types:
            return None  # handled as ambiguous

        lower = message.lower()
        has_youtube_url = bool(extract_youtube_urls(message))
        has_pdf = FileType.PDF in file_types

        if has_youtube_url or (_YOUTUBE_PATTERN.search(message) and has_pdf):
            return IntentResult(
                intent=IntentType.YOUTUBE_SUMMARIZE,
                confidence=0.95,
                reasoning="YouTube video summarization requested",
            )

        if _TRANSCRIBE_PATTERN.search(message) and FileType.AUDIO in file_types:
            return IntentResult(
                intent=IntentType.TRANSCRIBE,
                confidence=0.9,
                reasoning="Audio transcription requested",
            )

        if _SENTIMENT_PATTERN.search(message):
            return IntentResult(
                intent=IntentType.SENTIMENT_ANALYSIS,
                confidence=0.9,
                reasoning="Sentiment analysis keywords detected",
            )

        if _CODE_PATTERN.search(message):
            return IntentResult(
                intent=IntentType.CODE_ANALYSIS,
                confidence=0.85,
                reasoning="Code analysis keywords detected",
            )

        if _EXTRACT_PATTERN.search(message) and not _SUMMARIZE_PATTERN.search(message):
            return IntentResult(
                intent=IntentType.EXTRACT_TEXT,
                confidence=0.85,
                reasoning="Text extraction requested",
            )

        if _SUMMARIZE_PATTERN.search(message):
            return IntentResult(
                intent=IntentType.SUMMARIZE,
                confidence=0.9,
                reasoning="Summarization keywords detected",
            )

        if not message and not file_types:
            return IntentResult(
                intent=IntentType.AMBIGUOUS,
                confidence=1.0,
                follow_up_question="How can I help you today?",
            )

        return None

    def _ambiguous_for_files(self, file_types: list[FileType]) -> IntentResult:
        """Return follow-up when files are uploaded without instructions."""
        if not file_types:
            return IntentResult(
                intent=IntentType.AMBIGUOUS,
                confidence=1.0,
                follow_up_question="How can I help you today?",
            )

        if len(file_types) == 1:
            label = file_types[0].value
            question = f"What would you like me to do with the {label}?"
        else:
            labels = ", ".join(sorted({ft.value for ft in file_types}))
            question = f"What would you like me to do with these files ({labels})?"

        return IntentResult(
            intent=IntentType.AMBIGUOUS,
            confidence=1.0,
            follow_up_question=question,
        )

    def _detect_with_llm(
        self, message: str, file_types: list[FileType]
    ) -> IntentResult:
        """Classify intent using Groq; fall back to custom on failure."""
        file_desc = (
            ", ".join(ft.value for ft in file_types) if file_types else "none"
        )
        user_prompt = (
            f"User message: {message}\n"
            f"Uploaded file types: {file_desc}\n"
            "Classify the user's intent."
        )

        try:
            raw = groq_chat_completion(
                system_prompt=_LLM_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=self._settings.groq_model,
                temperature=0.0,
                max_tokens=256,
            )
            parsed = self._parse_llm_json(raw)
            intent_str = parsed.get("intent", "custom")
            valid_intents = {item.value for item in IntentType}
            intent = (
                IntentType(intent_str)
                if intent_str in valid_intents
                else IntentType.CUSTOM
            )

            if intent == IntentType.AMBIGUOUS:
                return IntentResult(
                    intent=IntentType.AMBIGUOUS,
                    confidence=float(parsed.get("confidence", 0.5)),
                    follow_up_question="Could you clarify what you'd like me to do?",
                    reasoning=parsed.get("reasoning"),
                )

            return IntentResult(
                intent=intent,
                confidence=float(parsed.get("confidence", 0.7)),
                reasoning=parsed.get("reasoning"),
            )
        except (ConfigurationError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("LLM intent detection failed, using fallback: %s", exc)
            return IntentResult(
                intent=IntentType.CUSTOM,
                confidence=0.5,
                reasoning=f"LLM fallback due to: {exc}",
            )

    def _parse_llm_json(self, raw: str) -> dict[str, object]:
        """Parse JSON from LLM output, stripping markdown fences if present."""
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0].strip()
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("LLM response is not a JSON object")
        return data
