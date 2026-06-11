"""Agent endpoint integration tests."""

from pathlib import Path

from fastapi.testclient import TestClient


def test_agent_pdf_only_returns_follow_up(
    upload_client: TestClient, sample_pdf_path: Path
) -> None:
    """PDF without message returns a follow-up question."""
    pdf_bytes = sample_pdf_path.read_bytes()
    response = upload_client.post(
        "/api/v1/agent",
        files=[("files", ("report.pdf", pdf_bytes, "application/pdf"))],
    )

    assert response.status_code == 200
    data = response.json()
    assert "follow_up" in data
    assert "pdf" in data["follow_up"].lower()


def test_agent_message_only(upload_client: TestClient) -> None:
    """Text-only agent request is accepted."""
    response = upload_client.post(
        "/api/v1/agent",
        data={"message": "Hello, what can you do?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "follow_up" in data or "response" in data


def test_agent_empty_request(upload_client: TestClient) -> None:
    """Empty agent request returns 400."""
    response = upload_client.post("/api/v1/agent")
    assert response.status_code == 400
