"""Tests for file type detection."""

import pytest

from app.utils.file_utils import FileType, detect_file_type


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("report.pdf", FileType.PDF),
        ("photo.PNG", FileType.IMAGE),
        ("recording.mp3", FileType.AUDIO),
        ("notes.txt", FileType.TEXT),
        ("archive.zip", FileType.UNKNOWN),
    ],
)
def test_detect_file_type(filename: str, expected: FileType) -> None:
    """File type is inferred from extension."""
    assert detect_file_type(filename) == expected
