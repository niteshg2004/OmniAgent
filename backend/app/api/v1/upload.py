from __future__ import annotations
from typing import Optional, Union
"""File upload routes."""

import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.deps import get_upload_service
from app.core.exceptions import UploadError
from app.schemas.upload import UploadResponse
from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "No files or message provided"},
        413: {"description": "File exceeds size limit"},
        415: {"description": "Unsupported file type"},
    },
)
async def upload_files(
    files: list[UploadFile] = File(default=[]),
    message: Optional[str] = Form(default=None),
    upload_service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    """Upload one or more files with an optional text message.

    Supported file types: PDF, images (png/jpg/jpeg/webp/gif/bmp/tiff),
    audio (mp3/wav/m4a/ogg/flac/webm), and text (txt/md/csv).

    Per-file failures are returned in ``errors`` while successful uploads
    appear in ``files`` (partial success).
    """
    result = await upload_service.process_upload(files=files, message=message)

    if not result.files and result.errors and not result.message:
        logger.warning("Upload failed for all %d file(s)", len(result.errors))
        raise UploadError(
            "All file uploads failed.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    logger.info(
        "Upload complete: success=%d errors=%d has_message=%s",
        len(result.files),
        len(result.errors),
        result.message is not None,
    )
    return result
