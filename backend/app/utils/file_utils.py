from __future__ import annotations
from typing import Optional, Union
"""File type detection and validation helpers."""

import mimetypes
import re
import uuid
from enum import Enum
from pathlib import Path


class FileType(str, Enum):
    """Supported upload file categories."""

    PDF = "pdf"
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    UNKNOWN = "unknown"


_PDF_EXTENSIONS = {".pdf"}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}
_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
_TEXT_EXTENSIONS = {".txt", ".md", ".csv"}

SUPPORTED_EXTENSIONS = (
    _PDF_EXTENSIONS | _IMAGE_EXTENSIONS | _AUDIO_EXTENSIONS | _TEXT_EXTENSIONS
)

_UNSAFE_FILENAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]")


def detect_file_type(filename: str, content_type: Optional[str] = None) -> FileType:
    """Detect file category from filename extension and optional MIME type.

    Args:
        filename: Original filename including extension.
        content_type: Optional MIME type from upload headers.

    Returns:
        FileType enum value.
    """
    suffix = Path(filename).suffix.lower()

    if suffix in _PDF_EXTENSIONS:
        return FileType.PDF
    if suffix in _IMAGE_EXTENSIONS:
        return FileType.IMAGE
    if suffix in _AUDIO_EXTENSIONS:
        return FileType.AUDIO
    if suffix in _TEXT_EXTENSIONS:
        return FileType.TEXT

    if content_type:
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            return detect_file_type(f"file{guessed}")

    return FileType.UNKNOWN


def is_supported_file(filename: str, content_type: Optional[str] = None) -> bool:
    """Return True if the file type is supported for upload.

    Args:
        filename: Original filename including extension.
        content_type: Optional MIME type from upload headers.

    Returns:
        True when the file maps to a known supported category.
    """
    return detect_file_type(filename, content_type) != FileType.UNKNOWN


def sanitize_filename(filename: str) -> str:
    """Return a safe basename with unsafe characters replaced.

    Args:
        filename: Raw filename from the client.

    Returns:
        Sanitized filename without directory components.
    """
    basename = Path(filename).name
    if not basename or basename in {".", ".."}:
        return "upload"

    stem = Path(basename).stem
    suffix = Path(basename).suffix.lower()
    safe_stem = _UNSAFE_FILENAME_PATTERN.sub("_", stem).strip("._") or "upload"
    return f"{safe_stem}{suffix}"


def build_stored_filename(original_filename: str) -> str:
    """Build a unique on-disk filename preserving the original extension.

    Args:
        original_filename: Client-provided filename.

    Returns:
        Unique filename in the form ``{uuid}_{sanitized_name}``.
    """
    safe_name = sanitize_filename(original_filename)
    return f"{uuid.uuid4().hex}_{safe_name}"
