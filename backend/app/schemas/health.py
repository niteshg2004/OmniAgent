from __future__ import annotations
"""Health and status response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., examples=["healthy"])
    service: str
    version: str


class RootResponse(BaseModel):
    """Root endpoint response."""

    message: str
    version: str
    docs_url: str = "/docs"
