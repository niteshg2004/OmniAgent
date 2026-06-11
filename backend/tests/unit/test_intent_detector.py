"""Intent detector unit tests."""

from app.planner.intent import IntentType
from app.planner.intent_detector import GroqIntentDetector
from app.schemas.agent import AgentRequest


def test_files_only_returns_follow_up() -> None:
    """Upload without message asks what to do with the file."""
    detector = GroqIntentDetector()
    request = AgentRequest(
        file_paths=["/tmp/report.pdf"],
        file_names=["report.pdf"],
    )

    result = detector.detect(request)

    assert result.intent == IntentType.AMBIGUOUS
    assert result.follow_up_question is not None
    assert "pdf" in result.follow_up_question.lower()


def test_summarize_keyword_detected() -> None:
    """Summarize keyword maps to SUMMARIZE intent."""
    detector = GroqIntentDetector()
    request = AgentRequest(
        message="Please summarize this document",
        file_paths=["/tmp/report.pdf"],
        file_names=["report.pdf"],
    )

    result = detector.detect(request)

    assert result.intent == IntentType.SUMMARIZE
    assert result.confidence >= 0.8


def test_youtube_in_pdf_message() -> None:
    """YouTube + PDF message maps to youtube_summarize."""
    detector = GroqIntentDetector()
    request = AgentRequest(
        message="Summarize the YouTube video mentioned in this PDF",
        file_paths=["/tmp/doc.pdf"],
        file_names=["doc.pdf"],
    )

    result = detector.detect(request)

    assert result.intent == IntentType.YOUTUBE_SUMMARIZE
