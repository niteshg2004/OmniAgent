from __future__ import annotations
"""Tool protocol and base class."""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.tools import ToolResult


class BaseTool(ABC):
    """Abstract base for all OmniAgent tools.

    Tools are pure: they accept typed inputs and return ToolResult.
    They must not import from api/, services/, or planner/.
    """

    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            ToolResult with success flag, data payload, and optional output_text.
        """
        ...
