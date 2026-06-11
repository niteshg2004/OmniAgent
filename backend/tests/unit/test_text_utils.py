"""Tests for text utilities."""

from app.utils.text_utils import extract_youtube_urls


def test_extract_youtube_urls_watch_format() -> None:
    """Extract standard watch URLs."""
    text = "See https://www.youtube.com/watch?v=dQw4w9WgXcQ for details"
    urls = extract_youtube_urls(text)
    assert len(urls) == 1
    assert "dQw4w9WgXcQ" in urls[0]


def test_extract_youtube_urls_short_format() -> None:
    """Extract youtu.be short URLs."""
    text = "Link: https://youtu.be/dQw4w9WgXcQ"
    urls = extract_youtube_urls(text)
    assert len(urls) == 1


def test_extract_youtube_urls_none_found() -> None:
    """Return empty list when no URLs present."""
    assert extract_youtube_urls("No links here") == []
