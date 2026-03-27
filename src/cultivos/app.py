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

from cultivos.api import all_routers
from cultivos.config import get_settings
from cultivos.middleware import register_error_handlers

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
        from cultivos.db.seeds import seed_ancestral_methods, seed_crops, seed_diseases, seed_fertilizers
        db_session = get_session_factory()()
        try:
            count = seed_fertilizers(db_session)
            if count:
                logger.info("Seeded %d fertilizer methods", count)
            count = seed_ancestral_methods(db_session)
            if count:
                logger.info("Seeded %d ancestral methods", count)
            count = seed_crops(db_session)
            if count:
                logger.info("Seeded %d crop types", count)
            count = seed_diseases(db_session)
            if count:
                logger.info("Seeded %d diseases", count)
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

    register_error_handlers(app)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers — registered from central api/__init__.py registry
    for r in all_routers:
        app.include_router(r)

    # Health check
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # Readiness probe — verifies DB connectivity
    @app.get("/api/readiness")
    def readiness():
        from sqlalchemy import text
        from cultivos.db.session import get_session_factory
        db = get_session_factory()()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ready"}
        except Exception:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        finally:
            db.close()

    # Serve frontend
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    if frontend_dir.exists():
        @app.get("/")
        async def serve_index():
            return FileResponse(frontend_dir / "index.html")

        @app.get("/intel")
        async def serve_intel():
            return FileResponse(frontend_dir / "intel.html")

        @app.get("/campo")
        async def serve_campo():
            return FileResponse(frontend_dir / "field.html")

        @app.get("/demo")
        async def serve_demo():
            return FileResponse(frontend_dir / "demo.html")

        app.mount("/", StaticFiles(directory=str(frontend_dir)), name="frontend")

    return app
