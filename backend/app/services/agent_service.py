from __future__ import annotations
"""Agent service — primary business logic entry point."""

import logging
from typing import Any

from app.planner.executor import PlanExecutor
from app.planner.intent import IntentDetector, IntentType
from app.planner.planner import Planner
from app.schemas.agent import AgentRequest, AgentResponse, FollowUpResponse

logger = logging.getLogger(__name__)


class AgentService:
    """Coordinates intent detection, planning, and execution."""

    def __init__(
        self,
        intent_detector: IntentDetector,
        planner: Planner,
        executor: PlanExecutor,
    ) -> None:
        self._intent_detector = intent_detector
        self._planner = planner
        self._executor = executor

    def process(self, request: AgentRequest) -> AgentResponse | FollowUpResponse:
        """Process an agent request end-to-end.

        Args:
            request: Validated request with optional message and file paths.

        Returns:
            FollowUpResponse when intent is ambiguous, otherwise AgentResponse.
        """
        logger.info(
            "Processing agent request: message=%s, files=%d",
            "present" if request.message else "none",
            len(request.file_paths),
        )

        intent = self._intent_detector.detect(request)

        if intent.intent == IntentType.AMBIGUOUS or intent.follow_up_question:
            logger.info("Ambiguous intent — returning follow-up question")
            return FollowUpResponse(follow_up=intent.follow_up_question or "What would you like me to do?")

        plan = self._planner.create_plan(request, intent)
        trace, context = self._executor.execute(plan, request)

        # Response text generation is implemented in Phase 7+
        response_text = context.get("response_text", "")

        metadata: dict[str, Any] = {
            "intent": intent.intent.value,
            "confidence": intent.confidence,
        }
        if intent.reasoning:
            metadata["reasoning"] = intent.reasoning

        # Add cost information if available
        total_cost = context.get("total_cost_usd", 0.0)
        if total_cost > 0:
            metadata["cost_usd"] = round(total_cost, 6)
            cost_breakdown = context.get("cost_breakdown", [])
            if cost_breakdown:
                metadata["cost_breakdown"] = {tool: round(cost, 6) for tool, cost in cost_breakdown}

        return AgentResponse(
            response=response_text,
            trace=trace.entries,
            metadata=metadata,
        )
