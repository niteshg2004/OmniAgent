from __future__ import annotations
"""Agent request and response schemas."""

from typing import Optional, Union, Any

from pydantic import BaseModel, Field

from app.schemas.trace import ToolTraceEntry


class AgentRequest(BaseModel):
    """Validated agent request after file uploads are processed."""

    message: Optional[str] = Field(
        default=None,
        description="User text instruction; may be None when only files are uploaded",
    )
    file_paths: list[str] = Field(
        default_factory=list,
        description="Absolute paths to uploaded files on disk",
    )
    file_names: list[str] = Field(
        default_factory=list,
        description="Original filenames corresponding to file_paths",
    )


class FollowUpResponse(BaseModel):
    """Response when user intent is ambiguous."""

    follow_up: str = Field(..., min_length=1)
    trace: list[ToolTraceEntry] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Final agent response with text output and execution trace."""

    response: str = Field(..., description="Text-only response to the user")
    trace: list[ToolTraceEntry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
