from __future__ import annotations
"""Text processing utilities."""

import re

_YOUTUBE_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)"
    r"([a-zA-Z0-9_-]{11})"
)


def extract_youtube_urls(text: str) -> list[str]:
    """Extract YouTube video URLs from text.

    Args:
        text: Raw text that may contain YouTube links.

    Returns:
        List of matched URL strings in order of appearance.
    """
    return [match.group(0) for match in _YOUTUBE_URL_PATTERN.finditer(text)]
