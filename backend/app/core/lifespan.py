from __future__ import annotations
"""Application lifespan — startup and shutdown hooks."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup and shutdown logic for the application."""
    settings = get_settings()

    setup_logging()
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Starting %s v%s (debug=%s, log_level=%s)",
        settings.app_name,
        settings.app_version,
        settings.debug,
        settings.log_level,
    )
    logger.info("Upload directory ready: %s", upload_path.resolve())

    yield

    logger.info("Shutting down %s", settings.app_name)
