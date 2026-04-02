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
        description=(
            "Agricultural Intelligence — precision farming platform.\n\n"
            "cultivOS transforms drone imagery (NDVI, thermal) and soil data into "
            "actionable regenerative agriculture recommendations for small and medium farms."
        ),
        contact={"name": "cultivOS", "url": "https://github.com/SebSanGar/cultivOS"},
        lifespan=_lifespan,
        openapi_tags=[
            {"name": "farms", "description": "Farm and field CRUD operations"},
            {"name": "auth", "description": "User registration and JWT authentication"},
            {"name": "ndvi", "description": "NDVI vegetation index analysis from drone imagery"},
            {"name": "thermal", "description": "Thermal stress detection from drone imagery"},
            {"name": "health", "description": "Crop health scoring and trend analysis"},
            {"name": "soil", "description": "Soil analysis records and composition tracking"},
            {"name": "weather", "description": "Weather observations and forecast integration"},
            {"name": "treatments", "description": "Treatment application records and effectiveness"},
            {"name": "intelligence", "description": "Cerebro AI field intelligence and regenerative scoring"},
            {"name": "dashboard", "description": "Aggregated farm dashboard data"},
            {"name": "alerts", "description": "Automated health, irrigation, and anomaly alerts"},
            {"name": "alert-config", "description": "Per-farm alert threshold configuration"},
            {"name": "notifications", "description": "Notification history and acknowledgement"},
            {"name": "knowledge", "description": "Organic fertilizers, ancestral methods, and crop database"},
            {"name": "diseases", "description": "Plant disease identification reference data"},
            {"name": "disease-risk", "description": "Weather-based disease risk assessment"},
            {"name": "irrigation", "description": "Irrigation scheduling optimization"},
            {"name": "rotation", "description": "Crop rotation planning and recommendations"},
            {"name": "carbon", "description": "Soil carbon MRV (measurement, reporting, verification)"},
            {"name": "microbiome", "description": "Soil microbiome health analysis"},
            {"name": "growth-stage", "description": "Crop growth stage tracking and phenology"},
            {"name": "flights", "description": "Drone flight logging and statistics"},
            {"name": "missions", "description": "Drone mission planning and path optimization"},
            {"name": "fusion", "description": "Multi-sensor data fusion analysis"},
            {"name": "yield", "description": "Crop yield prediction models"},
            {"name": "economics", "description": "Economic impact analysis per farm"},
            {"name": "feedback", "description": "Farmer feedback on treatment effectiveness"},
            {"name": "intervention-scores", "description": "Predictive intervention priority scoring"},
            {"name": "action-timeline", "description": "Weather-integrated prioritized action timeline"},
            {"name": "seasonal-alerts", "description": "Season-specific agricultural alerts and calendar"},
            {"name": "seasonal-comparison", "description": "Temporal vs dry season performance comparison"},
            {"name": "reports", "description": "PDF reports and CSV data exports"},
            {"name": "anomalies", "description": "Field-level anomaly detection for health and NDVI drops"},
            {"name": "completeness", "description": "Data completeness scoring per farm and field"},
            {"name": "status", "description": "Platform status, uptime, and data freshness overview"},
            {"name": "recommendations", "description": "Region-aware farm-level treatment recommendations"},
            {"name": "demo", "description": "Demo data endpoints for FODECIJAL walkthrough"},
        ],
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
        """Return a simple health check with the current API version."""
        return {"status": "ok", "version": "0.1.0"}

    # Readiness probe — verifies DB connectivity
    @app.get("/api/readiness")
    def readiness():
        """Verify database connectivity and return readiness status (503 if unavailable)."""
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

        @app.get("/conocimiento")
        async def serve_knowledge():
            """Ancestral knowledge base — methods, crops, and natural fertilizers."""
            return FileResponse(frontend_dir / "knowledge.html")

        @app.get("/login")
        async def serve_login():
            """Login and registration page."""
            return FileResponse(frontend_dir / "login.html")

        @app.get("/gestion")
        async def serve_management():
            """Farm and field management — CRUD operations for farms and fields."""
            return FileResponse(frontend_dir / "management.html")

        @app.get("/recomendaciones")
        async def serve_recommendations():
            """Farm recommendations — Cerebro treatment recommendations per field."""
            return FileResponse(frontend_dir / "recommendations.html")

        @app.get("/vuelos")
        async def serve_flights():
            """Drone flight log — mission history, fleet stats, and field coverage."""
            return FileResponse(frontend_dir / "flights.html")

        @app.get("/notificaciones")
        async def serve_notifications():
            """Notification history — alerts and recommendations across all farms."""
            return FileResponse(frontend_dir / "notifications.html")

        @app.get("/estado")
        async def serve_status():
            """Platform status dashboard — system health, data freshness, endpoint checks."""
            return FileResponse(frontend_dir / "status.html")

        @app.get("/importar-suelo")
        async def serve_soil_import():
            """Soil CSV import — bulk upload lab results for a field."""
            return FileResponse(frontend_dir / "soil-import.html")

        @app.get("/impacto-economico")
        async def serve_economic_impact():
            """Farm economic impact report — savings breakdown in MXN."""
            return FileResponse(frontend_dir / "economic-impact.html")

        @app.get("/docs-api")
        async def serve_api_docs():
            """Branded API reference page — links to Swagger, ReDoc, and OpenAPI."""
            return FileResponse(frontend_dir / "api-docs.html")

        @app.get("/suelo")
        async def serve_soil_history():
            """Soil analysis history — pH, organic matter, NPK trends over time."""
            return FileResponse(frontend_dir / "soil-history.html")

        @app.get("/historial")
        async def serve_timeline():
            """Field health history timeline — chronological health scores and treatments."""
            return FileResponse(frontend_dir / "timeline.html")

        @app.get("/onboarding")
        async def serve_onboarding():
            """Onboarding wizard — create a new farm with fields in 3 steps."""
            return FileResponse(frontend_dir / "onboarding.html")

        @app.get("/recorrido")
        async def serve_walkthrough():
            """FODECIJAL demo walkthrough — guided tour of Cerebro capabilities."""
            return FileResponse(frontend_dir / "walkthrough.html")

        @app.get("/alertas-config")
        async def serve_alert_config():
            """Alert configuration — custom thresholds per farm for health, NDVI, temperature."""
            return FileResponse(frontend_dir / "alert-config.html")

        @app.get("/termica")
        async def serve_thermal_dashboard():
            """Thermal stress dashboard — temperature analysis, stress zones, irrigation deficit."""
            return FileResponse(frontend_dir / "thermal-dashboard.html")

        @app.get("/regenerativo")
        async def serve_regenerative_scorecard():
            """Regenerative scorecard — practice score, breakdown, and recommendations per field."""
            return FileResponse(frontend_dir / "regenerative.html")

        @app.get("/carbono")
        async def serve_carbon_report():
            """Soil carbon sequestration report — SOC, CO2e, trends, and per-field breakdown."""
            return FileResponse(frontend_dir / "carbon.html")

        @app.get("/anomalias")
        async def serve_anomalies_center():
            """Anomaly detection center — health drops, NDVI drops, severity badges per field."""
            return FileResponse(frontend_dir / "anomalies.html")

        @app.get("/microbioma")
        async def serve_microbiome_health():
            """Soil microbiome health — respiration trends, fungi/bacteria ratios, biomass carbon."""
            return FileResponse(frontend_dir / "microbiome.html")

        @app.get("/rotacion")
        async def serve_rotation_planner():
            """Crop rotation planner — visual rotation calendar with soil benefit notes per season."""
            return FileResponse(frontend_dir / "rotation.html")

        @app.get("/mision")
        async def serve_mission_planner():
            """Drone mission planner — generate flight routes, waypoints, and flight parameters per field."""
            return FileResponse(frontend_dir / "mission.html")

        @app.get("/riego")
        async def serve_irrigation():
            """Irrigation scheduling — optimized watering calendar based on soil, weather, and thermal stress."""
            return FileResponse(frontend_dir / "irrigation.html")

        @app.get("/enfermedades")
        async def serve_disease():
            """Disease risk assessment — field-level risk from NDVI, thermal, and weather data with symptom identification."""
            return FileResponse(frontend_dir / "disease.html")

        @app.get("/tek")
        async def serve_tek():
            """Inteligencia Ancestral — farmer feedback validation — method trust scores from farmer feedback."""
            return FileResponse(frontend_dir / "tek.html")

        @app.get("/fusion")
        async def serve_fusion():
            """Sensor fusion validation — cross-sensor consistency matrix, contradictions, and confidence per field."""
            return FileResponse(frontend_dir / "fusion.html")

        @app.get("/inteligencia")
        async def serve_intelligence():
            """Comprehensive field intelligence — all Cerebro data for a single field in one unified view."""
            return FileResponse(frontend_dir / "intelligence.html")

        @app.get("/estaciones")
        async def serve_seasonal():
            """Seasonal comparison — temporal vs secas side-by-side metrics per field."""
            return FileResponse(frontend_dir / "seasonal.html")

        @app.get("/rendimiento")
        async def serve_yield():
            """Yield prediction — estimated harvest per field with uncertainty band."""
            return FileResponse(frontend_dir / "yield.html")

        @app.get("/acciones")
        async def serve_actions():
            """Action timeline — unified 7-day prioritized action list per field."""
            return FileResponse(frontend_dir / "actions.html")

        @app.get("/completitud")
        async def serve_completeness():
            """Data completeness dashboard — coverage by data source per farm."""
            return FileResponse(frontend_dir / "completitud.html")

        @app.get("/completitud-global")
        async def serve_completeness_global():
            """Global data completeness — cross-farm data gap overview."""
            return FileResponse(frontend_dir / "completitud-global.html")

        @app.get("/alertas-estacionales")
        async def serve_seasonal_alerts():
            """Seasonal alerts — Ancestral calendar-based crop alerts for current season."""
            return FileResponse(frontend_dir / "alertas-estacionales.html")

        @app.get("/intervenciones")
        async def serve_interventions():
            """Intervention ranking — treatments sorted by predicted impact and cost-effectiveness."""
            return FileResponse(frontend_dir / "intervenciones.html")

        @app.get("/efectividad")
        async def serve_effectiveness():
            """Treatment effectiveness report — cross-farm before/after health deltas."""
            return FileResponse(frontend_dir / "efectividad.html")

        @app.get("/regional")
        async def serve_regional():
            """Regional intelligence — aggregated farm data by state."""
            return FileResponse(frontend_dir / "regional.html")

        @app.get("/reportes")
        async def serve_reportes():
            """Portfolio report generation — multi-farm PDF reports with health, carbon, and economics."""
            return FileResponse(frontend_dir / "reportes.html")

        @app.get("/efectividad-global")
        async def serve_efectividad_global():
            """Global treatment effectiveness dashboard — bar charts, crop/region filters."""
            return FileResponse(frontend_dir / "efectividad-global.html")

        app.mount("/", StaticFiles(directory=str(frontend_dir)), name="frontend")

    return app
