from __future__ import annotations
"""Execution trace and planning schemas."""

from enum import Enum
from typing import Optional, Union, Any

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """Status of a single tool execution step."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ToolTraceEntry(BaseModel):
    """A single entry in the execution trace returned to the client."""

    step: int = Field(..., ge=1, description="Sequential step number starting at 1")
    tool: str = Field(..., min_length=1, description="Tool name invoked in this step")
    status: StepStatus
    error: Optional[str] = Field(default=None, description="Error message when status is failed")
    duration_ms: Optional[float] = Field(default=None, ge=0)


class PlanStep(BaseModel):
    """A single step in an execution plan before runtime."""

    step: int = Field(..., ge=1)
    tool: str = Field(..., min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class ExecutionTrace(BaseModel):
    """Ordered collection of tool trace entries for a request."""

    entries: list[ToolTraceEntry] = Field(default_factory=list)

    def add(
        self,
        step: int,
        tool: str,
        status: StepStatus,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Append a trace entry."""
        self.entries.append(
            ToolTraceEntry(
                step=step,
                tool=tool,
                status=status,
                error=error,
                duration_ms=duration_ms,
            )
        )

    def to_list(self) -> list[dict[str, Any]]:
        """Serialize trace to the API response format."""
        result: list[dict[str, Any]] = []
        for entry in self.entries:
            item: dict[str, Any] = {
                "step": entry.step,
                "tool": entry.tool,
                "status": entry.status.value,
            }
            if entry.error:
                item["error"] = entry.error
            if entry.duration_ms is not None:
                item["duration_ms"] = entry.duration_ms
            result.append(item)
        return result
