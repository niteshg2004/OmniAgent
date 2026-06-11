from __future__ import annotations
from typing import Optional, Union
"""Upload service — validates and persists uploaded files."""

import logging
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import (
    EmptyUploadError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.schemas.upload import UploadFileError, UploadedFileInfo, UploadResponse
from app.utils.file_utils import (
    build_stored_filename,
    detect_file_type,
    is_supported_file,
    sanitize_filename,
)

logger = logging.getLogger(__name__)

_READ_CHUNK_SIZE = 1024 * 1024  # 1 MB


class UploadService:
    """Handles multipart file uploads with validation and persistence."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._upload_dir = Path(settings.upload_dir)
        self._max_bytes = settings.max_upload_size_mb * 1024 * 1024

    async def process_upload(
        self,
        files: list[UploadFile],
        message: Optional[str] = None,
    ) -> UploadResponse:
        """Validate and save uploaded files, returning partial results on per-file failure.

        Args:
            files: Uploaded files from the multipart request.
            message: Optional user text submitted alongside files.

        Returns:
            UploadResponse with saved file metadata and per-file errors.

        Raises:
            EmptyUploadError: When no files and no message are provided.
        """
        normalized_message = message.strip() if message and message.strip() else None

        if not files and not normalized_message:
            raise EmptyUploadError()

        uploaded: list[UploadedFileInfo] = []
        errors: list[UploadFileError] = []

        self._upload_dir.mkdir(parents=True, exist_ok=True)

        for upload_file in files:
            filename = upload_file.filename or "unnamed"
            try:
                file_info = await self._save_file(upload_file)
                uploaded.append(file_info)
                logger.info(
                    "Saved upload: filename=%s path=%s size=%d type=%s",
                    file_info.filename,
                    file_info.stored_path,
                    file_info.size_bytes,
                    file_info.file_type.value,
                )
            except (FileTooLargeError, UnsupportedFileTypeError) as exc:
                logger.warning("Upload rejected for %s: %s", filename, exc.message)
                errors.append(UploadFileError(filename=filename, error=exc.message))
            except Exception as exc:
                logger.exception("Unexpected upload failure for %s", filename)
                errors.append(
                    UploadFileError(
                        filename=filename,
                        error=f"Failed to save file: {exc}",
                    )
                )

        status_message = self._build_status_message(uploaded, errors, normalized_message)

        return UploadResponse(
            files=uploaded,
            errors=errors,
            message=normalized_message,
            status_message=status_message,
        )

    async def _save_file(self, upload_file: UploadFile) -> UploadedFileInfo:
        """Validate and persist a single uploaded file.

        Args:
            upload_file: File from the multipart request.

        Returns:
            Metadata for the saved file.

        Raises:
            UnsupportedFileTypeError: When file type is not allowed.
            FileTooLargeError: When file exceeds size limit.
        """
        original_filename = upload_file.filename or "unnamed"
        content_type = upload_file.content_type

        if not is_supported_file(original_filename, content_type):
            file_type = detect_file_type(original_filename, content_type)
            raise UnsupportedFileTypeError(original_filename, file_type.value)

        stored_filename = build_stored_filename(original_filename)
        destination = self._upload_dir / stored_filename
        size_bytes = await self._write_file_stream(upload_file, destination)

        return UploadedFileInfo(
            filename=sanitize_filename(original_filename),
            content_type=content_type,
            size_bytes=size_bytes,
            stored_path=str(destination.resolve()),
            file_type=detect_file_type(original_filename, content_type),
        )

    async def _write_file_stream(self, upload_file: UploadFile, destination: Path) -> int:
        """Stream upload content to disk with size enforcement.

        Args:
            upload_file: Source upload file.
            destination: Target path on disk.

        Returns:
            Total bytes written.

        Raises:
            FileTooLargeError: When streamed content exceeds the limit.
        """
        size_bytes = 0
        filename = upload_file.filename or "unnamed"

        try:
            with destination.open("wb") as output:
                while True:
                    chunk = await upload_file.read(_READ_CHUNK_SIZE)
                    if not chunk:
                        break

                    size_bytes += len(chunk)
                    if size_bytes > self._max_bytes:
                        raise FileTooLargeError(
                            filename,
                            self._settings.max_upload_size_mb,
                        )
                    output.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await upload_file.close()

        if size_bytes == 0:
            destination.unlink(missing_ok=True)
            raise UnsupportedFileTypeError(filename, "empty")

        return size_bytes

    def _build_status_message(
        self,
        uploaded: list[UploadedFileInfo],
        errors: list[UploadFileError],
        message: Optional[str],
    ) -> str:
        """Build a human-readable summary of the upload result."""
        if uploaded and not errors:
            return f"Successfully uploaded {len(uploaded)} file(s)."
        if uploaded and errors:
            return (
                f"Uploaded {len(uploaded)} file(s) with {len(errors)} failure(s)."
            )
        if message and not uploaded:
            return "Text message received."
        return "No files were uploaded."
