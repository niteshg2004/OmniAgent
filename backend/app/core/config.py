from __future__ import annotations
"""Application configuration via environment variables."""

from functools import lru_cache
from typing import List, Literal, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "OmniAgent"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # LLM provider (Groq)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    # Upload limits
    max_upload_size_mb: int = Field(default=25, ge=1, le=100)
    upload_dir: str = "uploads"

    # Audio transcription
    whisper_model_size: str = "base"

    # CORS — comma-separated in .env, e.g. "http://localhost:3000,http://10.0.0.1:3000"
    cors_origins: Union[str, List[str]] = "*"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """Parse CORS_ORIGINS from a comma-separated string or list."""
        if isinstance(value, list):
            return value
        stripped = value.strip()
        if stripped == "*":
            return ["*"]
        return [origin.strip() for origin in stripped.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
