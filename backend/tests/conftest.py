"""Shared pytest fixtures."""

from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_app_settings
from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(create_app())


@pytest.fixture
def upload_settings(tmp_path: Path) -> Settings:
    """Settings with isolated upload directory and small size limit."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return Settings(
        upload_dir=str(upload_dir),
        max_upload_size_mb=1,
    )


@pytest.fixture
def upload_client(upload_settings: Settings) -> TestClient:
    """Test client with upload directory overridden."""
    app = create_app()
    app.dependency_overrides[get_app_settings] = lambda: upload_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> Path:
    """Create a temporary PDF with known text content."""
    pdf_path = tmp_path / "sample.pdf"
    document = fitz.open()
    try:
        page_one = document.new_page()
        page_one.insert_text((72, 72), "OmniAgent PDF test page one.")

        page_two = document.new_page()
        page_two.insert_text((72, 72), "Second page content here.")

        document.save(pdf_path)
    finally:
        document.close()

    return pdf_path


@pytest.fixture
def blank_pdf_path(tmp_path: Path) -> Path:
    """Create a PDF with a blank page (no extractable text)."""
    pdf_path = tmp_path / "blank.pdf"
    document = fitz.open()
    try:
        document.new_page()
        document.save(pdf_path)
    finally:
        document.close()
    return pdf_path


@pytest.fixture
def corrupt_pdf_path(tmp_path: Path) -> Path:
    """Create a file with a .pdf extension but invalid content."""
    pdf_path = tmp_path / "corrupt.pdf"
    pdf_path.write_bytes(b"not a real pdf file")
    return pdf_path
