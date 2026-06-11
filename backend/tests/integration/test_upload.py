"""Upload endpoint integration tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings


def test_upload_single_text_file(upload_client: TestClient, upload_settings: Settings) -> None:
    """A single text file is saved and metadata is returned."""
    response = upload_client.post(
        "/api/v1/upload",
        files=[("files", ("notes.txt", b"Hello OmniAgent", "text/plain"))],
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == "notes.txt"
    assert data["files"][0]["file_type"] == "text"
    assert data["files"][0]["size_bytes"] == 15
    assert Path(data["files"][0]["stored_path"]).exists()


def test_upload_multiple_files(upload_client: TestClient) -> None:
    """Multiple files can be uploaded in one request."""
    response = upload_client.post(
        "/api/v1/upload",
        files=[
            ("files", ("doc.txt", b"text content", "text/plain")),
            ("files", ("photo.png", b"\x89PNG\r\n", "image/png")),
        ],
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["files"]) == 2
    assert {f["file_type"] for f in data["files"]} == {"text", "image"}
    assert data["errors"] == []


def test_upload_with_message(upload_client: TestClient) -> None:
    """Optional text message is echoed in the response."""
    response = upload_client.post(
        "/api/v1/upload",
        data={"message": "Summarize these files"},
        files=[("files", ("report.txt", b"content", "text/plain"))],
    )

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Summarize these files"
    assert len(data["files"]) == 1


def test_upload_message_only(upload_client: TestClient) -> None:
    """Text-only submission is accepted without files."""
    response = upload_client.post(
        "/api/v1/upload",
        data={"message": "What can you do?"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "What can you do?"
    assert data["files"] == []
    assert data["status_message"] == "Text message received."


def test_upload_empty_request_returns_400(upload_client: TestClient) -> None:
    """Request with no files and no message is rejected."""
    response = upload_client.post("/api/v1/upload")
    assert response.status_code == 400
    assert response.json()["error_type"] == "empty_upload"


def test_upload_unsupported_file_returns_partial_error(upload_client: TestClient) -> None:
    """Unsupported files appear in errors while supported files still upload."""
    response = upload_client.post(
        "/api/v1/upload",
        files=[
            ("files", ("good.txt", b"ok", "text/plain")),
            ("files", ("bad.zip", b"PK", "application/zip")),
        ],
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == "good.txt"
    assert len(data["errors"]) == 1
    assert data["errors"][0]["filename"] == "bad.zip"


def test_upload_all_files_invalid_returns_400(upload_client: TestClient) -> None:
    """When every file fails and no message is provided, return 400."""
    response = upload_client.post(
        "/api/v1/upload",
        files=[("files", ("bad.exe", b"MZ", "application/octet-stream"))],
    )

    assert response.status_code == 400
    assert response.json()["error_type"] == "upload_error"


def test_upload_file_too_large(upload_client: TestClient) -> None:
    """Oversized files are reported in errors (limit is 1 MB in test fixture)."""
    oversized = b"x" * (1024 * 1024 + 1)
    response = upload_client.post(
        "/api/v1/upload",
        files=[("files", ("large.txt", oversized, "text/plain"))],
    )

    assert response.status_code == 400
    assert response.json()["error_type"] == "upload_error"
