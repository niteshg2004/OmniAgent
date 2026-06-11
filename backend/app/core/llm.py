from __future__ import annotations
from typing import Optional, Union, NamedTuple
"""Groq LLM client — used for intent detection and LLM-backed tools."""

import logging
from functools import lru_cache

from groq import AsyncGroq, Groq

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class LLMUsage(NamedTuple):
    """Token usage information from LLM response."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def _require_api_key(settings: Settings) -> str:
    """Return the Groq API key or raise a configuration error."""
    if not settings.groq_api_key:
        raise ConfigurationError(
            "Missing GROQ_API_KEY. Set it in your environment or .env file."
        )
    return settings.groq_api_key


@lru_cache
def get_groq_client() -> Groq:
    """Return a cached synchronous Groq client."""
    settings = get_settings()
    return Groq(api_key=_require_api_key(settings))


@lru_cache
def get_async_groq_client() -> AsyncGroq:
    """Return a cached asynchronous Groq client."""
    settings = get_settings()
    return AsyncGroq(api_key=_require_api_key(settings))


def groq_chat_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> str:
    """Run a chat completion against Groq and return the assistant text.

    Args:
        system_prompt: System message content.
        user_prompt: User message content.
        model: Model override; defaults to settings.groq_model.
        temperature: Sampling temperature.
        max_tokens: Maximum completion tokens.

    Returns:
        Assistant response text.

    Raises:
        ConfigurationError: When GROQ_API_KEY is missing.
        RuntimeError: When the API call fails.
    """
    text, _ = groq_chat_completion_with_usage(
        system_prompt, user_prompt, model=model, temperature=temperature, max_tokens=max_tokens
    )
    return text


def groq_chat_completion_with_usage(
    system_prompt: str,
    user_prompt: str,
    *,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> tuple[str, LLMUsage]:
    """Run a chat completion against Groq and return text + usage info.

    Args:
        system_prompt: System message content.
        user_prompt: User message content.
        model: Model override; defaults to settings.groq_model.
        temperature: Sampling temperature.
        max_tokens: Maximum completion tokens.

    Returns:
        Tuple of (assistant text, usage information).

    Raises:
        ConfigurationError: When GROQ_API_KEY is missing.
        RuntimeError: When the API call fails.
    """
    settings = get_settings()
    client = get_groq_client()
    model_name = model or settings.groq_model

    logger.info("Groq chat completion: model=%s", model_name)

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Groq returned an empty response")

        usage = LLMUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )
        return content.strip(), usage
    except ConfigurationError:
        raise
    except Exception as exc:
        logger.error("Groq chat completion failed: %s", exc)
        raise RuntimeError(f"LLM request failed: {exc}") from exc
