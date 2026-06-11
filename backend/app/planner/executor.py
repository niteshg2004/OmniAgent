from __future__ import annotations
"""Plan execution — runs tools sequentially and builds execution trace."""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.agent import AgentRequest
from app.schemas.trace import ExecutionTrace, PlanStep


class PlanExecutor(ABC):
    """Executes a plan step-by-step, logging each tool invocation."""

    @abstractmethod
    def execute(
        self,
        plan: list[PlanStep],
        request: AgentRequest,
    ) -> tuple[ExecutionTrace, dict[str, Any]]:
        """Run each plan step in order.

        Args:
            plan: Ordered execution plan from Planner.
            request: Original agent request for file paths and context.

        Returns:
            Tuple of (execution trace, accumulated context dict for response generation).
            Continues on failure when partial results are still useful.
        """
        ...
