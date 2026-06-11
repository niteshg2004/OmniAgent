from __future__ import annotations
"""Agent processing routes."""

import logging
from typing import Optional, Union

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.deps import get_agent_service, get_upload_service
from app.core.exceptions import EmptyUploadError
from app.schemas.agent import AgentRequest, AgentResponse, FollowUpResponse
from app.services.agent_service import AgentService
from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


@router.post(
    "/agent",
    response_model=Union[AgentResponse, FollowUpResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "No files or message provided"},
    },
)
async def process_agent(
    message: Optional[str] = Form(default=None),
    files: list[UploadFile] = File(default=[]),
    upload_service: UploadService = Depends(get_upload_service),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentResponse | FollowUpResponse:
    """Process a multimodal agent request.

    Accepts an optional text message and one or more files (PDF, image, audio, text).
    Detects intent, plans tool execution, runs tools, and returns a text response
    with a full execution trace.
    """
    upload_result = await upload_service.process_upload(files=files, message=message)

    if not upload_result.files and not upload_result.message:
        raise EmptyUploadError()

    agent_request = AgentRequest(
        message=upload_result.message,
        file_paths=[f.stored_path for f in upload_result.files],
        file_names=[f.filename for f in upload_result.files],
    )

    logger.info(
        "Agent request: message=%s files=%d upload_errors=%d",
        "yes" if agent_request.message else "no",
        len(agent_request.file_paths),
        len(upload_result.errors),
    )

    result = agent_service.process(agent_request)

    if isinstance(result, FollowUpResponse):
        return result

    if upload_result.errors:
        error_summary = "; ".join(
            f"{e.filename}: {e.error}" for e in upload_result.errors
        )
        result.metadata["upload_errors"] = error_summary

    return result
