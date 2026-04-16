"""
FastAPI application factory for cultivOS.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from cultivos.api import all_routers, is_public_router
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
        from cultivos.db.seeds import seed_agronomist_tips, seed_ancestral_methods, seed_crop_varieties, seed_crops, seed_diseases, seed_farmer_vocabulary, seed_fertilizers
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
            count = seed_crop_varieties(db_session)
            if count:
                logger.info("Seeded %d crop varieties", count)
            count = seed_agronomist_tips(db_session)
            if count:
                logger.info("Seeded %d agronomist tips", count)
            count = seed_farmer_vocabulary(db_session)
            if count:
                logger.info("Seeded %d farmer vocabulary entries", count)
        finally:
            db_session.close()
    yield


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers on every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://*.tile.openstreetmap.org; "
            "connect-src 'self'; "
            "font-src 'self' https://cdn.jsdelivr.net"
        )
        return response


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
            {"name": "alert-history", "description": "Cross-farm alert history timeline combining SMS and system alerts"},
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
            {"name": "farmer-impact", "description": "Farmer journey impact metrics and health improvement"},
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
            {"name": "phenology", "description": "Crop phenology calendar and growth stage timelines"},
            {"name": "photos", "description": "Crop photo upload and visual analysis"},
            {"name": "demo", "description": "Demo data endpoints for FODECIJAL walkthrough"},
            {"name": "cooperatives", "description": "Cooperative (farmer group) management and aggregate dashboards"},
            {"name": "executive", "description": "Platform-wide executive KPIs and multi-farm overview"},
            {"name": "system", "description": "Detailed system health and operational status"},
            {"name": "regions", "description": "Region-aware agricultural profiles (climate, soil, crops, currency)"},
            {"name": "predictions", "description": "Per-field AI prediction accuracy tracking (MAPE and resolved vs pending)"},
            {"name": "risk-map", "description": "Per-field risk heatmap combining health, weather, disease, and thermal scores"},
            {"name": "treatment-effectiveness", "description": "Per-field treatment cost and health delta — measurable ROI for each organic intervention"},
            {"name": "harvests", "description": "Harvest yield records and prediction accuracy closure — links actual yields to AI predictions"},
            {"name": "observations", "description": "Farmer ground-truth observations — completes the data loop (drone + sensor + farmer eyes). Required for WhatsApp integration."},
            {"name": "tek-adoption", "description": "Farm-level ancestral method adoption log — records which farmers adopted which traditional practices on which fields."},
            {"name": "water", "description": "Water use efficiency — stress index, optimal irrigation mm, and liters wasted per field"},
            {"name": "fields", "description": "Global field queries across all farms — crop type listing and filtering"},
        ],
    )

    register_error_handlers(app)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers — registered from central api/__init__.py registry.
    # Non-public routers are mounted with a session-wide `get_current_user`
    # dependency. When AUTH_ENABLED is false (default for dev/tests) the
    # dependency returns None and behavior is unchanged. When AUTH_ENABLED
    # is true the route 401s on an unauthenticated caller. Per-route
    # farm_id ownership checks remain a follow-up.
    from cultivos.auth import get_current_user
    for r in all_routers:
        if is_public_router(r):
            app.include_router(r)
        else:
            app.include_router(r, dependencies=[Depends(get_current_user)])

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

        @app.get("/exportar")
        async def serve_exportar():
            """Data export center — CSV and PDF downloads for health, soil, treatments, flights."""
            return FileResponse(frontend_dir / "exportar.html")

        @app.get("/calendario")
        async def serve_calendario():
            """Crop phenology calendar — Gantt-like growth stage timelines per crop."""
            return FileResponse(frontend_dir / "calendario.html")

        @app.get("/mapa")
        async def serve_mapa():
            """Interactive field map — farm locations, field boundaries, health-coded polygons."""
            return FileResponse(frontend_dir / "mapa.html")

        @app.get("/efectividad-global")
        async def serve_efectividad_global():
            """Global treatment effectiveness dashboard — bar charts, crop/region filters."""
            return FileResponse(frontend_dir / "efectividad-global.html")

        @app.get("/clima")
        async def serve_clima():
            """Weather dashboard — 7-day forecast, temperature/rainfall charts, drought alerts per farm."""
            return FileResponse(frontend_dir / "clima.html")

        @app.get("/comparar")
        async def serve_comparar():
            """Farm comparison tool — side-by-side health, yield, soil quality for 2-3 farms."""
            return FileResponse(frontend_dir / "comparar.html")

        @app.get("/resumen")
        async def serve_resumen():
            """Executive portfolio summary — total hectares, avg health, ROI projection for investors."""
            return FileResponse(frontend_dir / "resumen.html")

        @app.get("/flota")
        async def serve_flota():
            """Drone fleet status — battery, flight hours, maintenance, coverage per drone."""
            return FileResponse(frontend_dir / "flota.html")

        @app.get("/whatsapp-demo")
        async def serve_whatsapp_demo():
            """WhatsApp demo simulator — mock farmer-AI chat interaction in Spanish."""
            return FileResponse(frontend_dir / "whatsapp-demo.html")

        @app.get("/historial-alertas")
        async def serve_historial_alertas():
            """Alert history timeline — chronological view of all alerts per farm."""
            return FileResponse(frontend_dir / "historial-alertas.html")

        @app.get("/confianza-tratamientos")
        async def serve_confianza_tratamientos():
            """Treatment trust scores — ranked treatments by farmer feedback confidence."""
            return FileResponse(frontend_dir / "confianza-tratamientos.html")

        @app.get("/reporte-fodecijal")
        async def serve_reporte_fodecijal():
            """FODECIJAL grant report — generate and download technical narrative PDF."""
            return FileResponse(frontend_dir / "reporte-fodecijal.html")

        @app.get("/demo-fodecijal")
        async def serve_demo_fodecijal():
            """Guided FODECIJAL demo — 8-step walkthrough of key platform capabilities."""
            return FileResponse(frontend_dir / "demo-fodecijal.html")

        @app.get("/plataforma")
        async def serve_plataforma():
            """Platform overview — categorized grid of all cultivOS pages and features."""
            return FileResponse(frontend_dir / "plataforma.html")

        @app.get("/api-status")
        async def serve_api_status():
            """System health dashboard — API versions, DB counts, test count for grant reviewers."""
            return FileResponse(frontend_dir / "api-status.html")

        @app.get("/trayectoria")
        async def serve_trayectoria():
            """Health trajectory — trend, projection, and treatment correlation per field."""
            return FileResponse(frontend_dir / "trayectoria.html")

        @app.get("/cerebro-analytics")
        async def serve_cerebro_analytics():
            """Cerebro AI analytics — decision log, accuracy, and activity trends."""
            return FileResponse(frontend_dir / "cerebro-analytics.html")

        @app.get("/precision-ia")
        async def serve_precision_ia():
            """Prediction accuracy tracker — compare AI forecasts vs actual outcomes."""
            return FileResponse(frontend_dir / "precision-ia.html")

        @app.get("/impacto-agricultor")
        async def serve_impacto_agricultor():
            """Farmer impact summary — per-farm journey metrics and health improvement."""
            return FileResponse(frontend_dir / "impacto-agricultor.html")

        @app.get("/ejecutivo")
        async def serve_ejecutivo():
            """Multi-farm executive dashboard — platform-wide KPIs for grant reviewers and investors."""
            return FileResponse(frontend_dir / "ejecutivo.html")

        @app.get("/cooperativa")
        async def serve_cooperativa():
            """Cooperative management — farmer groups with aggregate health/carbon/economic rollups."""
            return FileResponse(frontend_dir / "cooperativa.html")

        @app.get("/calculadora-suelo")
        async def serve_calculadora_suelo():
            """Soil amendment calculator — organic amendments prescription from current soil values."""
            return FileResponse(frontend_dir / "calculadora-suelo.html")

        @app.get("/fotos")
        async def serve_fotos():
            """Crop photo analysis — upload field photos for instant visual classification."""
            return FileResponse(frontend_dir / "fotos.html")

        @app.get("/coop-evidencia")
        async def serve_coop_evidencia():
            """Cooperative FODECIJAL evidence pack — 5 KPIs, 3 pillar bars, strength/weakness per coop."""
            return FileResponse(frontend_dir / "coop-evidencia.html")

        @app.get("/coop-progreso-mensual")
        async def serve_coop_progreso_mensual():
            """Cooperative monthly progress — Chart.js line chart of avg health + regen score per month."""
            return FileResponse(frontend_dir / "coop-progreso-mensual.html")

        @app.get("/historial-enfermedades")
        async def serve_historial_enfermedades():
            """Field disease history — Chart.js bar chart of monthly diseases + recurring list (#215)."""
            return FileResponse(frontend_dir / "historial-enfermedades.html")

        @app.get("/nutrientes-suelo")
        async def serve_nutrientes_suelo():
            """Field soil nutrient trajectory — Chart.js multi-line N/P/K/OM trend per month (#221)."""
            return FileResponse(frontend_dir / "nutrientes-suelo.html")

        @app.get("/hitos-regenerativos")
        async def serve_hitos_regenerativos():
            """Farm regen milestones — 7-step regenerative progression per farm (#223)."""
            return FileResponse(frontend_dir / "hitos-regenerativos.html")

        @app.get("/roi-tratamientos")
        async def serve_roi_tratamientos():
            """Farm treatment ROI — cost per health point per treatment type + recommendation (#222)."""
            return FileResponse(frontend_dir / "roi-tratamientos.html")

        @app.get("/correlacion-ndvi")
        async def serve_correlacion_ndvi():
            """Field NDVI-health correlation — scatter plot + strength pill per field (#224)."""
            return FileResponse(frontend_dir / "correlacion-ndvi.html")

        @app.get("/efectividad-intervenciones")
        async def serve_efectividad_intervenciones():
            """Field intervention effectiveness — doughnut chart + best/worst treatment cards (#225)."""
            return FileResponse(frontend_dir / "efectividad-intervenciones.html")

        @app.get("/indice-estres")
        async def serve_indice_estres():
            """Field stress composite index — big number + 3 sub-score gauges (#233)."""
            return FileResponse(frontend_dir / "indice-estres.html")

        @app.get("/frescura-sensores")
        async def serve_frescura_sensores():
            """Sensor data freshness — per-field sensor grid with stale indicators (#229)."""
            return FileResponse(frontend_dir / "frescura-sensores.html")

        @app.get("/escalaciones-alertas")
        async def serve_escalaciones_alertas():
            """Alert escalation backlog — unaddressed alerts sorted by days pending (#230)."""
            return FileResponse(frontend_dir / "escalaciones-alertas.html")

        @app.get("/prioridad-riesgo")
        async def serve_prioridad_riesgo():
            """Risk-weighted field priority — ranked cards by urgency (#228)."""
            return FileResponse(frontend_dir / "prioridad-riesgo.html")

        @app.get("/diversidad-cultivos")
        async def serve_diversidad_cultivos():
            """Cooperative crop diversity — Shannon index, top crops bar chart, per-farm table (#231)."""
            return FileResponse(frontend_dir / "diversidad-cultivos.html")

        @app.get("/preparacion-fodecijal")
        async def serve_preparacion_fodecijal():
            """Cooperative FODECIJAL readiness — 5-pillar readiness score with grade (#237)."""
            return FileResponse(frontend_dir / "preparacion-fodecijal.html")

        @app.get("/prediccion-salud")
        async def serve_prediccion_salud():
            """Field 30-day health prediction — current vs predicted scores with trend and confidence (#238)."""
            return FileResponse(frontend_dir / "prediccion-salud.html")

        @app.get("/plan-accion")
        async def serve_plan_accion():
            """Field weekly action plan — prioritized actions by stress, treatment, and TEK (#239)."""
            return FileResponse(frontend_dir / "plan-accion.html")

        @app.get("/reporte-anual")
        async def serve_reporte_anual():
            """Farm annual report — year-over-year performance per field with KPIs (#232)."""
            return FileResponse(frontend_dir / "reporte-anual.html")

        @app.get("/resiliencia")
        async def serve_resiliencia():
            """Field crop resilience score — composite 0-100 with 4 component bars and Spanish grade (#234)."""
            return FileResponse(frontend_dir / "resiliencia.html")

        @app.get("/alineacion-tek")
        async def serve_alineacion_tek():
            """Field TEK sensor alignment — ancestral practices vs sensor data with score ring and practice cards (#240)."""
            return FileResponse(frontend_dir / "alineacion-tek.html")

        @app.get("/ranking-miembros")
        async def serve_ranking_miembros():
            """Cooperative member farm ranking — leaderboard with medal badges and composite scores (#236)."""
            return FileResponse(frontend_dir / "ranking-miembros.html")

        @app.get("/benchmark-regional")
        async def serve_benchmark_regional():
            """Farm regional benchmark — own health vs state peers with percentile rank (#235)."""
            return FileResponse(frontend_dir / "benchmark-regional.html")

        @app.get("/alertas-clima")
        async def serve_alertas_clima():
            """Field weather alert history — alerts per type with trend and severity chart (#241)."""
            return FileResponse(frontend_dir / "alertas-clima.html")

        app.mount("/", StaticFiles(directory=str(frontend_dir)), name="frontend")

    return app
