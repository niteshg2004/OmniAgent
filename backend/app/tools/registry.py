from __future__ import annotations
"""Tool registry for discovery and invocation by name."""

import logging
from typing import Any

from app.core.exceptions import ToolExecutionError
from app.schemas.tools import ToolResult
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry mapping tool names to tool instances."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance by its name."""
        if tool.name in self._tools:
            logger.warning("Overwriting existing tool registration: %s", tool.name)
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def get(self, name: str) -> BaseTool:
        """Retrieve a tool by name."""
        if name not in self._tools:
            raise ToolExecutionError(name, f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        """Return registered tool names."""
        return sorted(self._tools.keys())

    def run(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a registered tool by name."""
        tool = self.get(name)
        logger.info("Executing tool: %s", name)
        return tool.run(**kwargs)
