from __future__ import annotations
"""Tool input/output schemas."""

from typing import Optional, Union, Any

from pydantic import BaseModel, Field

from app.schemas.cost import CostEstimate


class ToolResult(BaseModel):
    """Standardized result from any tool execution."""

    tool_name: str = Field(..., min_length=1)
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    output_text: Optional[str] = Field(
        default=None,
        description="Primary text output passed to downstream tools",
    )
    cost_estimate: Optional[CostEstimate] = Field(
        default=None,
        description="Cost estimate for LLM-backed tools",
    )
