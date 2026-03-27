"""
FastAPI application factory for cultivOS.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from cultivos.api.auth import router as auth_router
from cultivos.api.dashboard import router as dashboard_router
from cultivos.api.farms import router as farms_router
from cultivos.api.health import router as health_router
from cultivos.api.intel import router as intel_router
from cultivos.api.irrigation import router as irrigation_router
from cultivos.api.knowledge import router as knowledge_router
from cultivos.api.ndvi import router as ndvi_router
from cultivos.api.rotation import router as rotation_router
from cultivos.api.soil import router as soil_router
from cultivos.api.thermal import router as thermal_router
from cultivos.api.treatments import router as treatments_router
from cultivos.api.weather import router as weather_router
from cultivos.config import get_settings

logger = logging.getLogger(__name__)
_access_log = logging.getLogger("cultivos.access")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """FastAPI lifespan: initialize database."""
    is_testing = os.environ.get("DB_URL", "").startswith("sqlite:///:memory:")
    if not is_testing:
        from cultivos.db.session import get_engine, get_session_factory
        get_engine()  # creates tables
        logger.info("Database initialized")
        # Seed knowledge base data
        from cultivos.db.seeds import seed_fertilizers
        db_session = get_session_factory()()
        try:
            count = seed_fertilizers(db_session)
            if count:
                logger.info("Seeded %d fertilizer methods", count)
        finally:
            db_session.close()
    yield


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000
        _access_log.info(
            "%s %s -> %d  (%.0fms)",
            request.method, request.url.path, response.status_code, duration_ms,
        )
        return response


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI app."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )

    app = FastAPI(
        title="cultivOS API",
        version="0.1.0",
        description="Agricultural Intelligence — precision farming platform",
        lifespan=_lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(farms_router)
    app.include_router(health_router)
    app.include_router(intel_router)
    app.include_router(irrigation_router)
    app.include_router(knowledge_router)
    app.include_router(ndvi_router)
    app.include_router(rotation_router)
    app.include_router(soil_router)
    app.include_router(thermal_router)
    app.include_router(treatments_router)
    app.include_router(weather_router)

    # Health check
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # Serve frontend
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    if frontend_dir.exists():
        @app.get("/")
        async def serve_index():
            return FileResponse(frontend_dir / "index.html")

        @app.get("/intel")
        async def serve_intel():
            return FileResponse(frontend_dir / "intel.html")

        app.mount("/", StaticFiles(directory=str(frontend_dir)), name="frontend")

    return app
