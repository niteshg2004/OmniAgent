from __future__ import annotations
"""OmniAgent FastAPI application entry point."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_app_settings
from app.api.exception_handlers import register_exception_handlers
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.lifespan import lifespan
from app.core.middleware import RequestLoggingMiddleware
from app.schemas.health import HealthResponse, RootResponse

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Multimodal agentic AI system for text, PDF, image, and audio processing"
        ),
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    app.include_router(api_router, prefix="/api")

    @app.get("/", response_model=RootResponse, tags=["root"])
    def root(settings: Settings = Depends(get_app_settings)) -> RootResponse:
        """Root endpoint with service metadata."""
        return RootResponse(
            message=f"{settings.app_name} is running",
            version=settings.app_version,
        )

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
        """Health check for load balancers and deployment platforms."""
        return HealthResponse(
            status="healthy",
            service=settings.app_name,
            version=settings.app_version,
        )

    return app


app = create_app()
