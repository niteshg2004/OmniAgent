"""YouTube transcript fetching."""

from __future__ import annotations

import logging
import re
from typing import Optional
from xml.etree.ElementTree import ParseError

from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

from app.schemas.tools import ToolResult
from app.tools.base import BaseTool
from app.utils.text_utils import extract_youtube_urls

logger = logging.getLogger(__name__)

TOOL_NAME = "youtube_transcript"

_VIDEO_ID_PATTERN = re.compile(r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})")


def _extract_video_id(url_or_text: str) -> Optional[str]:
    """Extract a YouTube video ID from a URL or text containing a URL."""
    urls = extract_youtube_urls(url_or_text)
    if urls:
        target = urls[0]
        match = _VIDEO_ID_PATTERN.search(target)
        if match:
            return match.group(1)
    
    # Try direct pattern match on the input
    match = _VIDEO_ID_PATTERN.search(url_or_text)
    return match.group(1) if match else None


def fetch_youtube_transcript(url_or_text: str) -> tuple[str, str]:
    """Fetch the transcript for a YouTube video.

    Args:
        url_or_text: YouTube URL or text containing a URL.

    Returns:
        Tuple of (transcript text, video id).

    Raises:
        ValueError: If no video ID can be resolved.
        RuntimeError: If the transcript cannot be fetched.
    """
    video_id = _extract_video_id(url_or_text)
    if not video_id:
        raise ValueError(
            "No YouTube URL found. Please provide a YouTube link "
            "(e.g., https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID)"
        )

    try:
        api = YouTubeTranscriptApi()
        transcript_obj = api.fetch(video_id, languages=["en"])

        text_parts = []
        for snippet in transcript_obj:
            if hasattr(snippet, 'text'):
                text_parts.append(snippet.text)
            elif isinstance(snippet, dict) and 'text' in snippet:
                text_parts.append(snippet['text'])

        text = " ".join(text_parts).strip()
        if not text:
            raise RuntimeError(
                f"Video {video_id} has transcripts but they appear to be empty."
            )
        return text, video_id

    except TranscriptsDisabled:
        raise RuntimeError(
            f"Transcripts are disabled for video {video_id}. "
            "The video creator has disabled transcripts."
        )
    except NoTranscriptFound:
        raise RuntimeError(
            f"No transcripts found for video {video_id}. "
            "This video may not have captions available."
        )
    except VideoUnavailable:
        raise RuntimeError(f"Video {video_id} is unavailable or has been removed.")
    except ParseError as exc:
        logger.error(
            "XML parsing error for video %s: %s", video_id, exc
        )
        raise RuntimeError(
            f"Failed to parse transcript data for video {video_id}. "
            "YouTube may have changed their response format or the request was blocked."
        ) from exc
    except Exception as exc:
        error_msg = str(exc).lower()
        logger.exception("YouTube API error for video %s: %s", video_id, exc)
        if "xml" in error_msg or "parse" in error_msg or "element" in error_msg or "blocked" in error_msg or "attribute" in error_msg:
            raise RuntimeError(
                f"Failed to parse or fetch transcript for video {video_id}. "
                "YouTube may be blocking the request or the library may need updating."
            ) from exc
        raise RuntimeError(f"Failed to fetch transcript for video {video_id}: {exc}") from exc


class YoutubeTranscriptTool(BaseTool):
    """Fetch transcripts from YouTube videos."""

    name = TOOL_NAME
    description = "Fetch the transcript of a YouTube video from a URL or embedded link."

    def run(self, **kwargs: object) -> ToolResult:
        """Fetch transcript using ``url`` or ``text`` containing a YouTube link.

        Args:
            **kwargs: ``url`` (str) or ``text`` (str) with a YouTube URL.

        Returns:
            ToolResult with transcript in ``output_text``.
        """
        url = kwargs.get("url")
        text = kwargs.get("text")
        source = url if isinstance(url, str) and url else text

        if not source or not isinstance(source, str):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: url or text",
            )

        logger.info("Fetching YouTube transcript")

        try:
            transcript, video_id = fetch_youtube_transcript(source)
            logger.info(
                "YouTube transcript fetched: video_id=%s chars=%d",
                video_id,
                len(transcript),
            )
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"video_id": video_id, "char_count": len(transcript)},
                output_text=transcript,
            )
        except ValueError as exc:
            logger.error("YouTube URL resolution failed: %s", exc)
            return ToolResult(tool_name=self.name, success=False, error=str(exc))
        except RuntimeError as exc:
            logger.error("YouTube transcript fetch failed: %s", exc)
            return ToolResult(tool_name=self.name, success=False, error=str(exc))
        except Exception as exc:
            logger.exception("Unexpected YouTube transcript error")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Unexpected error fetching YouTube transcript: {exc}",
            )
