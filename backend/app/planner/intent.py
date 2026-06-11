from __future__ import annotations
from typing import Optional, Union
"""Intent detection — determines user goal or requests clarification."""

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.agent import AgentRequest


class IntentType(str, Enum):
    """High-level intent categories."""

    AMBIGUOUS = "ambiguous"
    SUMMARIZE = "summarize"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    EXTRACT_TEXT = "extract_text"
    TRANSCRIBE = "transcribe"
    YOUTUBE_SUMMARIZE = "youtube_summarize"
    CODE_ANALYSIS = "code_analysis"
    CUSTOM = "custom"


class IntentResult(BaseModel):
    """Output of intent detection."""

    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    follow_up_question: Optional[str] = Field(
        default=None,
        description="Set when intent is ambiguous; returned to user instead of executing",
    )
    reasoning: Optional[str] = Field(default=None, description="Brief explanation for debugging")


class IntentDetector(ABC):
    """Detects user intent from message and uploaded files."""

    @abstractmethod
    def detect(self, request: AgentRequest) -> IntentResult:
        """Analyze request and return intent or a follow-up question.

        Args:
            request: Validated agent request with message and file paths.

        Returns:
            IntentResult with intent type or follow_up_question when ambiguous.
        """
        ...
