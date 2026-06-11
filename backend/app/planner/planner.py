from __future__ import annotations
"""Execution plan generation."""

from abc import ABC, abstractmethod

from app.planner.intent import IntentResult
from app.schemas.agent import AgentRequest
from app.schemas.trace import PlanStep


class Planner(ABC):
    """Generates minimal ordered execution plans from intent and context."""

    @abstractmethod
    def create_plan(self, request: AgentRequest, intent: IntentResult) -> list[PlanStep]:
        """Build the shortest valid tool chain for the given intent.

        Args:
            request: Agent request with files and message.
            intent: Detected intent from IntentDetector.

        Returns:
            Ordered list of PlanStep objects. Empty if intent is ambiguous.
        """
        ...
