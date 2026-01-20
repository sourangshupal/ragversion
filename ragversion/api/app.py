"""FastAPI application factory."""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ragversion import AsyncVersionTracker, __version__
from ragversion.api.config import APIConfig
from ragversion.api.dependencies import set_tracker
from ragversion.api.models import HealthCheckResponse, ErrorResponse
from ragversion.api.routes import documents, versions, tracking, statistics
from ragversion.web import routes as web_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup: Initialize tracker
    tracker = app.state.tracker
    if tracker:
        await tracker.initialize()
        set_tracker(tracker)

    yield

    # Shutdown: Close tracker
    if tracker:
        await tracker.close()


def create_app(
    tracker: AsyncVersionTracker,
    config: APIConfig = None,
) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        tracker: AsyncVersionTracker instance to use
        config: API configuration (defaults to APIConfig())

    Returns:
        Configured FastAPI application
    """
    if config is None:
        config = APIConfig()

    app = FastAPI(
        title=config.title,
        version=config.version,
        description="REST API for RAGVersion - Version tracking for RAG applications",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Store tracker and config in app state
    app.state.tracker = tracker
    app.state.config = config

    # Add CORS middleware
    if config.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal server error",
                detail=str(exc),
                timestamp=datetime.utcnow(),
            ).model_dump(),
        )

    # Health check endpoint
    @app.get(
        "/api/health",
        response_model=HealthCheckResponse,
        tags=["health"],
        summary="Health check",
        description="Check API server health and storage backend status",
    )
    async def health_check():
        """Health check endpoint."""
        try:
            # Test storage backend by attempting to get statistics
            await tracker.get_statistics(days=1)
            storage_healthy = True
        except Exception:
            storage_healthy = False

        return HealthCheckResponse(
            status="healthy" if storage_healthy else "degraded",
            version=__version__,
            storage_backend=tracker.storage.__class__.__name__,
            storage_healthy=storage_healthy,
            timestamp=datetime.utcnow(),
        )

    # Register API routers (with /api prefix)
    app.include_router(documents.router, prefix="/api")
    app.include_router(versions.router, prefix="/api")
    app.include_router(tracking.router, prefix="/api")
    app.include_router(statistics.router, prefix="/api")

    # Register web UI routes (at root)
    app.include_router(web_routes.router)

    return app
