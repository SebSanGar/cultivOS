# cultivOS

Precision agricultural intelligence for Jalisco — ancestral knowledge validated with sensor data.

cultivOS makes regenerative farming practices economically viable by proving with data that they work. Drones capture NDVI and thermal imagery, AI processes it into a health score, and the farmer gets a WhatsApp message in plain Spanish telling them exactly what to do.

## The Thesis

Farmers don't need to be convinced of ancestral practices philosophically. They need to see the yield data and income math that makes it the rational choice. cultivOS makes that math visible — in WhatsApp, in plain Spanish, with color instead of numbers.

## What's Built

**345 tests. 26 API endpoints. 4 frontend pages.**

| Module | What it does |
|--------|-------------|
| Health scoring | Composite 0-100 score from NDVI + soil + thermal + trend |
| NDVI processing | Multispectral band math → vegetation index → zone classification |
| Thermal stress | Drone thermal imagery → water stress map + irrigation deficit flag |
| Treatment recommendations | Organic-only, Spanish, cost in MXN per hectare |
| Crop rotation planner | 3-season plan based on last crop, Jalisco seasons, soil health |
| Irrigation optimizer | 7-day water schedule from weather + soil + thermal |
| Yield prediction | SIAP baselines for 11 Jalisco crops, health-adjusted with confidence ranges |
| Disease/pest detection | NDVI anomaly patterns classified as disease vs pest vs nutrient |
| Fertilizer knowledge base | 10 organic methods queryable by crop type |
| Ancestral practices | 8 traditional Mexican methods (milpa, chinampas, terrazas, etc.) |
| Crop database | 11 Jalisco crops with growing seasons and companion planting |
| Soil microbiome | Microbial diversity tracking, auto-classification |
| Weather integration | OpenWeather forecasts correlated with field conditions |
| Farm dashboard | Spanish-first, mobile-friendly, color-coded health indicators |
| Field detail page | Full Cerebro intelligence drill-down per field |
| Intelligence dashboard | Dark-theme admin/researcher view with cross-farm analytics |
| Demo page | Guided walkthrough of the full platform for investors/partners |
| Role-based auth | JWT with admin/researcher/farmer roles |
| PDF reports | Spanish-language farm reports for FIRA loans |
| CSV import/export | Bulk soil data import, farm data export with Spanish headers |
| SMS alerts | Irrigation alerts with deduplication |
| Drone mission planning | Boustrophedon waypoints from field boundary polygons |
| Seasonal comparison | Temporal vs secas analysis with year-over-year |
| Treatment tracking | Before/after health score delta per treatment |

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy / Pydantic v2
- **Frontend**: Vanilla HTML/CSS/JS (no build step) + Chart.js
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Processing**: NumPy (NDVI, thermal)
- **Auth**: JWT with role-based access
- **Testing**: pytest (345 tests)

## Run

```bash
./run.sh
# → http://localhost:8000       Farm dashboard
# → http://localhost:8000/intel  Intelligence dashboard
# → http://localhost:8000/demo   Platform walkthrough
```

Or manually:
```bash
PYTHONPATH="$PWD/src" uvicorn cultivos.app:create_app --factory --port 8000
```

## Test

```bash
PYTHONPATH="$PWD/src" pytest tests/ -q
```

## Team

- **Sebastian Sanchez Garcia** — CEO / Co-founder. Guadalajara-born, Toronto-based.
- **Mubeen Zulfiqar** — CTO / Co-founder. MSc CS Waterloo.
- **Arshia Heravi** — Software Engineer / Co-founder. Creator of AutoAgent.

## Partnerships

- **ITESO** (Guadalajara) — Academic validation partner. Drone lab + campus garden.

## Funding

- **FODECIJAL 2026** — $2M MXN applied (Cerebro AI validation, deadline May 14)
- **Impulsora de Innovación** — $6M MXN target (hardware + operations)

## Architecture

```
src/cultivos/
├── app.py              # FastAPI factory
├── config.py           # Pydantic settings from .env
├── auth.py             # JWT + role-based access
├── api/                # 26 route files (thin — HTTP only)
├── services/
│   ├── crop/           # ndvi.py, thermal.py, health.py, disease.py
│   ├── intelligence/   # recommendations.py, rotation.py, irrigation.py, analytics.py
│   ├── pipeline/       # ingest.py (CSV import)
│   └── weather_client.py
├── models/             # Pydantic schemas
└── db/                 # SQLAlchemy ORM + session

frontend/
├── index.html          # Farm dashboard
├── field.html          # Field detail (Cerebro drill-down)
├── intel.html          # Intelligence dashboard (admin/researcher)
├── demo.html           # Platform walkthrough
├── app.js, field.js, intel.js
└── styles.css
```

## License

Proprietary — CultivOS Mexico S.A. de C.V.
