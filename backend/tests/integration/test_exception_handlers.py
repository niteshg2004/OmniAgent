"""Exception handler integration tests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.exception_handlers import register_exception_handlers
from app.core.exceptions import ConfigurationError, ToolExecutionError


def _build_test_app() -> FastAPI:
    """Build a minimal app with exception handlers registered."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/config-error")
    def raise_config_error() -> None:
        raise ConfigurationError("Missing GROQ_API_KEY")

    @app.get("/tool-error")
    def raise_tool_error() -> None:
        raise ToolExecutionError("pdf_extractor", "Failed to parse PDF")

    return app


def test_configuration_error_returns_503() -> None:
    """Configuration errors map to 503 Service Unavailable."""
    client = TestClient(_build_test_app())
    response = client.get("/config-error")
    assert response.status_code == 503
    assert response.json()["error_type"] == "configuration_error"


def test_tool_execution_error_returns_422() -> None:
    """Tool execution errors map to 422 Unprocessable Entity."""
    client = TestClient(_build_test_app())
    response = client.get("/tool-error")
    assert response.status_code == 422
    body = response.json()
    assert body["error_type"] == "tool_execution_error"
    assert body["tool"] == "pdf_extractor"
