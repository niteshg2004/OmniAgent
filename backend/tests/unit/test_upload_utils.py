"""Upload utility unit tests."""

from app.utils.file_utils import build_stored_filename, sanitize_filename


def test_sanitize_filename_removes_path_components() -> None:
    """Directory traversal attempts are stripped to basename."""
    assert sanitize_filename("../../etc/passwd") == "passwd"


def test_sanitize_filename_replaces_unsafe_characters() -> None:
    """Unsafe characters are replaced with underscores."""
    assert sanitize_filename("my file (1).txt") == "my_file__1.txt"


def test_build_stored_filename_is_unique() -> None:
    """Stored filenames include a UUID prefix."""
    first = build_stored_filename("report.pdf")
    second = build_stored_filename("report.pdf")
    assert first != second
    assert first.endswith("_report.pdf")
