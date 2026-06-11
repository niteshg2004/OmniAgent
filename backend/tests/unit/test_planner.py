"""Planner unit tests."""

from app.planner.intent import IntentResult, IntentType
from app.planner.omni_planner import OmniAgentPlanner
from app.schemas.agent import AgentRequest


def test_plan_summarize_includes_extractor_and_summarizer() -> None:
    """Summarize intent produces extraction + summarizer steps."""
    planner = OmniAgentPlanner()
    request = AgentRequest(
        message="Summarize this document",
        file_paths=["/tmp/report.pdf"],
        file_names=["report.pdf"],
    )
    intent = IntentResult(intent=IntentType.SUMMARIZE, confidence=0.9)

    plan = planner.create_plan(request, intent)

    assert len(plan) == 2
    assert plan[0].tool == "pdf_extractor"
    assert plan[1].tool == "summarizer"
    assert plan[1].params["text"] == "$prev"


def test_plan_youtube_from_pdf() -> None:
    """YouTube summarize from PDF produces 3-step plan."""
    planner = OmniAgentPlanner()
    request = AgentRequest(
        message="Summarize the YouTube video mentioned in this PDF",
        file_paths=["/tmp/doc.pdf"],
        file_names=["doc.pdf"],
    )
    intent = IntentResult(intent=IntentType.YOUTUBE_SUMMARIZE, confidence=0.95)

    plan = planner.create_plan(request, intent)

    assert [step.tool for step in plan] == [
        "pdf_extractor",
        "youtube_transcript",
        "summarizer",
    ]


def test_plan_ambiguous_returns_empty() -> None:
    """Ambiguous intent yields no plan steps."""
    planner = OmniAgentPlanner()
    request = AgentRequest(file_paths=["/tmp/a.pdf"], file_names=["a.pdf"])
    intent = IntentResult(
        intent=IntentType.AMBIGUOUS,
        confidence=1.0,
        follow_up_question="What would you like me to do with the pdf?",
    )

    assert planner.create_plan(request, intent) == []
