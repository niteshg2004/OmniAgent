"""Configuration unit tests."""

from app.core.config import Settings


def test_cors_origins_parsed_from_comma_separated_string() -> None:
    """CORS_ORIGINS env value is split into a list."""
    settings = Settings(cors_origins="http://localhost:3000, http://localhost:8000")
    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://localhost:8000",
    ]


def test_cors_origins_wildcard() -> None:
    """Single asterisk is preserved as wildcard."""
    settings = Settings(cors_origins="*")
    assert settings.cors_origins == ["*"]


def test_groq_model_default() -> None:
    """Default Groq model is a capable general-purpose model."""
    settings = Settings()
    assert settings.groq_model == "llama-3.3-70b-versatile"
