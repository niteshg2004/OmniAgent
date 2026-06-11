"""Executor unit tests."""

from unittest.mock import MagicMock

from app.planner.omni_executor import OmniAgentExecutor
from app.schemas.agent import AgentRequest
from app.schemas.tools import ToolResult
from app.schemas.trace import PlanStep, StepStatus


def test_executor_records_success_and_failure() -> None:
    """Executor builds trace with success and failed steps."""
    registry = MagicMock()
    registry.run.side_effect = [
        ToolResult(
            tool_name="pdf_extractor",
            success=True,
            output_text="PDF content",
        ),
        ToolResult(
            tool_name="summarizer",
            success=False,
            error="LLM unavailable",
        ),
    ]

    executor = OmniAgentExecutor(registry)
    plan = [
        PlanStep(step=1, tool="pdf_extractor", params={"file_path": "$file:0"}),
        PlanStep(step=2, tool="summarizer", params={"text": "$prev"}),
    ]
    request = AgentRequest(
        message="Summarize",
        file_paths=["/tmp/a.pdf"],
        file_names=["a.pdf"],
    )

    trace, context = executor.execute(plan, request)

    assert len(trace.entries) == 2
    assert trace.entries[0].status == StepStatus.SUCCESS
    assert trace.entries[1].status == StepStatus.FAILED
    assert "PDF content" in context["response_text"]


def test_executor_resolves_file_reference() -> None:
    """$file:0 param is resolved to the request file path."""
    registry = MagicMock()
    registry.run.return_value = ToolResult(
        tool_name="text_reader",
        success=True,
        output_text="hello",
    )

    executor = OmniAgentExecutor(registry)
    plan = [
        PlanStep(step=1, tool="text_reader", params={"file_path": "$file:0"}),
    ]
    request = AgentRequest(
        file_paths=["/data/notes.txt"],
        file_names=["notes.txt"],
    )

    executor.execute(plan, request)

    registry.run.assert_called_once_with("text_reader", file_path="/data/notes.txt")
