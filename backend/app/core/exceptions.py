"""Domain-specific exception hierarchy."""

from __future__ import annotations
from typing import Optional


class OmniAgentError(Exception):
    """Base exception for all OmniAgent domain errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ConfigurationError(OmniAgentError):
    """Raised when required configuration is missing or invalid."""


class ToolExecutionError(OmniAgentError):
    """Raised when a tool fails during execution."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(message)


class IntentAmbiguousError(OmniAgentError):
    """Raised when user intent cannot be determined; triggers follow-up question."""

    def __init__(self, follow_up_question: str) -> None:
        self.follow_up_question = follow_up_question
        super().__init__(follow_up_question)


class PlanExecutionError(OmniAgentError):
    """Raised when plan execution fails irrecoverably."""


class UploadError(OmniAgentError):
    """Base exception for file upload errors."""

    status_code: int = 400

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class EmptyUploadError(UploadError):
    """Raised when the request contains no files and no message."""

    def __init__(self) -> None:
        super().__init__(
            "At least one file or a text message is required.",
            status_code=400,
        )


class FileTooLargeError(UploadError):
    """Raised when an uploaded file exceeds the configured size limit."""

    def __init__(self, filename: str, max_size_mb: int) -> None:
        self.filename = filename
        self.max_size_mb = max_size_mb
        super().__init__(
            f"File '{filename}' exceeds the maximum size of {max_size_mb} MB.",
            status_code=413,
        )


class UnsupportedFileTypeError(UploadError):
    """Raised when an uploaded file type is not supported."""

    def __init__(self, filename: str, file_type: str) -> None:
        self.filename = filename
        self.file_type = file_type
        super().__init__(
            f"File '{filename}' has unsupported type '{file_type}'.",
            status_code=415,
        )
