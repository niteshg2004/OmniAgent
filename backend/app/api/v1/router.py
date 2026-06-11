from __future__ import annotations
"""Aggregates all v1 API routers."""

from fastapi import APIRouter

from app.api.v1 import agent, health, upload

api_router = APIRouter(prefix="/v1")

api_router.include_router(health.router)
api_router.include_router(upload.router)
api_router.include_router(agent.router)
