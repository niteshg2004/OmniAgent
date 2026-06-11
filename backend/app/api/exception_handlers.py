from __future__ import annotations
"""Global exception handlers for FastAPI."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    ConfigurationError,
    EmptyUploadError,
    FileTooLargeError,
    IntentAmbiguousError,
    OmniAgentError,
    PlanExecutionError,
    ToolExecutionError,
    UnsupportedFileTypeError,
    UploadError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain and fallback exception handlers on the app."""

    @app.exception_handler(EmptyUploadError)
    async def empty_upload_handler(
        request: Request, exc: EmptyUploadError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_type": "empty_upload"},
        )

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(
        request: Request, exc: FileTooLargeError
    ) -> JSONResponse:
        logger.warning("File too large on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "error_type": "file_too_large",
                "filename": exc.filename,
                "max_size_mb": exc.max_size_mb,
            },
        )

    @app.exception_handler(UnsupportedFileTypeError)
    async def unsupported_file_type_handler(
        request: Request, exc: UnsupportedFileTypeError
    ) -> JSONResponse:
        logger.warning("Unsupported file type on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "error_type": "unsupported_file_type",
                "filename": exc.filename,
                "file_type": exc.file_type,
            },
        )

    @app.exception_handler(UploadError)
    async def upload_error_handler(
        request: Request, exc: UploadError
    ) -> JSONResponse:
        logger.warning("Upload error on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_type": "upload_error"},
        )

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(
        request: Request, exc: ConfigurationError
    ) -> JSONResponse:
        logger.error("Configuration error on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=503,
            content={"detail": exc.message, "error_type": "configuration_error"},
        )

    @app.exception_handler(IntentAmbiguousError)
    async def intent_ambiguous_handler(
        request: Request, exc: IntentAmbiguousError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "follow_up": exc.follow_up_question,
                "trace": [],
            },
        )

    @app.exception_handler(ToolExecutionError)
    async def tool_execution_error_handler(
        request: Request, exc: ToolExecutionError
    ) -> JSONResponse:
        logger.warning(
            "Tool execution failed on %s: tool=%s error=%s",
            request.url.path,
            exc.tool_name,
            exc.message,
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.message,
                "error_type": "tool_execution_error",
                "tool": exc.tool_name,
            },
        )

    @app.exception_handler(PlanExecutionError)
    async def plan_execution_error_handler(
        request: Request, exc: PlanExecutionError
    ) -> JSONResponse:
        logger.error("Plan execution failed on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "error_type": "plan_execution_error"},
        )

    @app.exception_handler(OmniAgentError)
    async def omniagent_error_handler(
        request: Request, exc: OmniAgentError
    ) -> JSONResponse:
        logger.error("Domain error on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "error_type": "domain_error"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        settings = get_settings()
        logger.exception("Unhandled error on %s", request.url.path)

        detail = str(exc) if settings.debug else "An internal server error occurred."
        return JSONResponse(
            status_code=500,
            content={"detail": detail, "error_type": "internal_error"},
        )
