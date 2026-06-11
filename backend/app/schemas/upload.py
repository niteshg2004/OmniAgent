from __future__ import annotations
from typing import Optional, Union
"""Upload-related API schemas."""

from pydantic import BaseModel, Field

from app.utils.file_utils import FileType


class UploadedFileInfo(BaseModel):
    """Metadata for a single uploaded file."""

    filename: str
    content_type: Optional[str] = None
    size_bytes: int = Field(..., ge=0)
    stored_path: str
    file_type: FileType


class UploadFileError(BaseModel):
    """Error details for a file that failed to upload."""

    filename: str
    error: str


class UploadResponse(BaseModel):
    """Response from the file upload endpoint."""

    files: list[UploadedFileInfo] = Field(default_factory=list)
    errors: list[UploadFileError] = Field(default_factory=list)
    message: Optional[str] = Field(
        default=None,
        description="Optional user text submitted with the upload",
    )
    status_message: str = "Upload processed"
