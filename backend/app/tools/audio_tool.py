from __future__ import annotations
from typing import Optional, Union
"""Audio transcription using faster-whisper."""

import logging
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import Settings, get_settings
from app.schemas.tools import ToolResult
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

TOOL_NAME = "audio_transcriber"


@lru_cache
def _get_whisper_model(model_size: str) -> WhisperModel:
    """Load and cache the Whisper model (expensive; singleton per process)."""
    logger.info("Loading Whisper model: size=%s", model_size)
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_audio(file_path: str, model_size: Optional[str] = None) -> tuple[str, str]:
    """Transcribe speech from an audio file.

    Args:
        file_path: Path to an audio file.
        model_size: Whisper model size override.

    Returns:
        Tuple of (transcript text, detected language code).

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If transcription fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    settings = get_settings()
    size = model_size or settings.whisper_model_size

    try:
        model = _get_whisper_model(size)
        segments, info = model.transcribe(str(path), beam_size=5)
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        language = info.language or "unknown"
        return transcript, language
    except Exception as exc:
        raise RuntimeError(f"Audio transcription failed: {exc}") from exc


class AudioTranscriberTool(BaseTool):
    """Transcribe audio files to text."""

    name = TOOL_NAME
    description = "Transcribe speech from audio files using faster-whisper."

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    def run(self, **kwargs: object) -> ToolResult:
        """Transcribe audio at ``file_path``.

        Args:
            **kwargs: Expected key ``file_path`` (str).

        Returns:
            ToolResult with transcript in ``output_text``.
        """
        file_path = kwargs.get("file_path")
        if not file_path or not isinstance(file_path, str):
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Missing required parameter: file_path",
            )

        logger.info("Transcribing audio: path=%s", file_path)

        try:
            transcript, language = transcribe_audio(
                file_path, self._settings.whisper_model_size
            )
            logger.info(
                "Audio transcription complete: path=%s chars=%d language=%s",
                file_path,
                len(transcript),
                language,
            )
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "file_path": file_path,
                    "char_count": len(transcript),
                    "language": language,
                    "has_text": len(transcript) > 0,
                },
                output_text=transcript,
            )
        except (FileNotFoundError, ValueError) as exc:
            logger.error("Audio transcription validation failed: %s", exc)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                data={"file_path": file_path},
            )
        except RuntimeError as exc:
            logger.error("Audio transcription failed: %s", exc)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                data={"file_path": file_path},
            )
        except Exception as exc:
            logger.exception("Unexpected audio transcription error: path=%s", file_path)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Unexpected error during audio transcription: {exc}",
                data={"file_path": file_path},
            )
