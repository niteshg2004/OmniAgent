"""Health and root endpoint integration tests."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Root health check returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "OmniAgent"
    assert data["version"] == "1.0.0"


def test_api_v1_health_endpoint(client: TestClient) -> None:
    """Versioned health check under /api/v1/health."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "OmniAgent"


def test_root_endpoint(client: TestClient) -> None:
    """Root endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "OmniAgent" in data["message"]
    assert data["version"] == "1.0.0"
    assert data["docs_url"] == "/docs"
