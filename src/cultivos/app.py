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

from cultivos.config import get_settings

logger = logging.getLogger(__name__)
_access_log = logging.getLogger("cultivos.access")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """FastAPI lifespan: initialize database."""
    is_testing = os.environ.get("DB_URL", "").startswith("sqlite:///:memory:")
    if not is_testing:
        from cultivos.db.session import get_engine
        get_engine()  # creates tables
        logger.info("Database initialized")
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
        title="Kitchen Intelligence API",
        version="0.1.0",
        description="Hungry-Cooks.com — Kitchen operations intelligence platform",
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

    # Health check
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # API routers
    from cultivos.api.recipes import router as recipes_router
    from cultivos.api.ingredients import router as ingredients_router
    from cultivos.api.suppliers import router as suppliers_router
    from cultivos.api.production import router as production_router
    from cultivos.api.waste import router as waste_router
    from cultivos.api.financial import router as financial_router
    from cultivos.api.locations import router as locations_router

    app.include_router(recipes_router, prefix="/api", tags=["recipes"])
    app.include_router(ingredients_router, prefix="/api", tags=["ingredients"])
    app.include_router(suppliers_router, prefix="/api", tags=["suppliers"])
    app.include_router(production_router, prefix="/api", tags=["production"])
    app.include_router(waste_router, prefix="/api", tags=["waste"])
    app.include_router(financial_router, prefix="/api", tags=["financial"])
    app.include_router(locations_router, prefix="/api", tags=["locations"])

    # Serve frontend
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    if frontend_dir.exists():
        @app.get("/")
        async def serve_index():
            return FileResponse(frontend_dir / "index.html")

        app.mount("/", StaticFiles(directory=str(frontend_dir)), name="frontend")

    return app
