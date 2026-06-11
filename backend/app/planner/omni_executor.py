from __future__ import annotations
"""Concrete plan executor with execution trace."""

import logging
import time
from typing import Any

from app.planner.executor import PlanExecutor
from app.schemas.agent import AgentRequest
from app.schemas.trace import ExecutionTrace, PlanStep, StepStatus
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

_LLM_OUTPUT_TOOLS = {"summarizer", "sentiment_analyzer", "code_analyzer"}


class OmniAgentExecutor(PlanExecutor):
    """Executes plans sequentially, recording trace and accumulating context."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        plan: list[PlanStep],
        request: AgentRequest,
    ) -> tuple[ExecutionTrace, dict[str, Any]]:
        """Run each plan step in order, logging trace entries."""
        trace = ExecutionTrace()
        context: dict[str, Any] = {
            "file_paths": request.file_paths,
            "file_names": request.file_names,
            "step_outputs": {},
            "combined_text": "",
            "last_output_text": "",
            "response_text": "",
            "total_cost_usd": 0.0,
            "cost_breakdown": [],  # List of (tool, cost_usd)
        }

        if not plan:
            logger.warning("Empty execution plan")
            return trace, context

        for plan_step in plan:
            start = time.perf_counter()
            resolved_params = self._resolve_params(plan_step.params, context, request)

            logger.info(
                "Executing plan step %d: tool=%s params_keys=%s",
                plan_step.step,
                plan_step.tool,
                list(resolved_params.keys()),
            )

            try:
                result = self._registry.run(plan_step.tool, **resolved_params)
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                error_msg = str(exc)
                trace.add(
                    step=plan_step.step,
                    tool=plan_step.tool,
                    status=StepStatus.FAILED,
                    error=error_msg,
                    duration_ms=duration_ms,
                )
                logger.error(
                    "Step %d tool=%s failed: %s (%.1fms)",
                    plan_step.step,
                    plan_step.tool,
                    error_msg,
                    duration_ms,
                )
                continue

            duration_ms = (time.perf_counter() - start) * 1000

            if result.success:
                trace.add(
                    step=plan_step.step,
                    tool=plan_step.tool,
                    status=StepStatus.SUCCESS,
                    duration_ms=duration_ms,
                )
                output = result.output_text or ""
                context["step_outputs"][plan_step.step] = output
                context["last_output_text"] = output
                context["combined_text"] = self._merge_text(
                    context["combined_text"], output
                )
                if plan_step.tool in _LLM_OUTPUT_TOOLS:
                    context["response_text"] = output

                # Track cost if available
                if result.cost_estimate:
                    cost_usd = result.cost_estimate.total_cost_usd
                    context["total_cost_usd"] += cost_usd
                    context["cost_breakdown"].append((plan_step.tool, cost_usd))
                    logger.info(
                        "Step %d tool=%s cost: $%.6f (%.1fms)",
                        plan_step.step,
                        plan_step.tool,
                        cost_usd,
                        duration_ms,
                    )
                else:
                    logger.info(
                        "Step %d tool=%s succeeded (%.1fms)",
                        plan_step.step,
                        plan_step.tool,
                        duration_ms,
                    )
            else:
                trace.add(
                    step=plan_step.step,
                    tool=plan_step.tool,
                    status=StepStatus.FAILED,
                    error=result.error,
                    duration_ms=duration_ms,
                )
                logger.warning(
                    "Step %d tool=%s failed: %s (%.1fms)",
                    plan_step.step,
                    plan_step.tool,
                    result.error,
                    duration_ms,
                )

        if not context["response_text"]:
            context["response_text"] = (
                context["last_output_text"] or context["combined_text"] or ""
            )

        if not context["response_text"]:
            failed = [e for e in trace.entries if e.status == StepStatus.FAILED]
            if failed:
                context["response_text"] = (
                    f"I was unable to complete the request. "
                    f"Error at step {failed[0].step} ({failed[0].tool}): "
                    f"{failed[0].error}"
                )
            else:
                context["response_text"] = "No content could be extracted or generated."

        return trace, context

    def _resolve_params(
        self,
        params: dict[str, Any],
        context: dict[str, Any],
        request: AgentRequest,
    ) -> dict[str, Any]:
        """Resolve ``$file:N``, ``$prev``, and ``$step:N`` parameter references."""
        resolved: dict[str, Any] = {}
        for key, value in params.items():
            if not isinstance(value, str):
                resolved[key] = value
                continue

            if value.startswith("$file:"):
                index = int(value.split(":")[1])
                resolved[key] = request.file_paths[index]
            elif value == "$prev":
                resolved[key] = context.get("last_output_text", "")
            elif value.startswith("$step:"):
                step_index = int(value.split(":")[1])
                resolved[key] = context["step_outputs"].get(step_index, "")
            else:
                resolved[key] = value

        return resolved

    def _merge_text(self, existing: str, new_text: str) -> str:
        """Concatenate text outputs from multiple extraction steps."""
        if not new_text:
            return existing
        if not existing:
            return new_text
        return f"{existing}\n\n{new_text}"
