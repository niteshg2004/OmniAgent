"""Groq LLM client unit tests."""

import pytest

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.core.llm import _require_api_key


def test_require_api_key_raises_when_missing() -> None:
    """Missing Groq API key raises ConfigurationError."""
    settings = Settings(groq_api_key=None)
    with pytest.raises(ConfigurationError, match="GROQ_API_KEY"):
        _require_api_key(settings)


def test_require_api_key_returns_key_when_set() -> None:
    """Configured API key is returned."""
    settings = Settings(groq_api_key="gsk_test_key")
    assert _require_api_key(settings) == "gsk_test_key"
