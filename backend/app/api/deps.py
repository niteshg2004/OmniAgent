from __future__ import annotations
"""FastAPI dependency injection providers."""

from functools import lru_cache

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.planner.intent_detector import GroqIntentDetector
from app.planner.omni_executor import OmniAgentExecutor
from app.planner.omni_planner import OmniAgentPlanner
from app.services.agent_service import AgentService
from app.services.upload_service import UploadService
from app.tools.bootstrap import create_tool_registry
from app.tools.registry import ToolRegistry


@lru_cache
def get_app_settings() -> Settings:
    """Provide application settings to route handlers."""
    return get_settings()


@lru_cache
def get_tool_registry() -> ToolRegistry:
    """Provide the default tool registry."""
    return create_tool_registry()


def get_upload_service(
    settings: Settings = Depends(get_app_settings),
) -> UploadService:
    """Provide an UploadService instance."""
    return UploadService(settings)


def get_agent_service(
    settings: Settings = Depends(get_app_settings),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> AgentService:
    """Provide a fully wired AgentService."""
    return AgentService(
        intent_detector=GroqIntentDetector(settings),
        planner=OmniAgentPlanner(),
        executor=OmniAgentExecutor(registry),
    )
