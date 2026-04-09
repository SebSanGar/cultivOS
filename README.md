# cultivOS

**Precision agricultural intelligence for small and medium farms — ancestral knowledge validated with sensor data.**

[![Tests](https://img.shields.io/badge/tests-2539%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red)](#license)

cultivOS turns drone imagery, soil sensors, and weather data into plain-Spanish farm advice delivered over WhatsApp. Drones capture NDVI and thermal, our intelligence layer ("Cerebro") scores field health, and farmers get a color-coded recommendation they can act on the same day — no agronomy degree required.

**Not a drone company.** We use third-party hardware (DJI). Our value is the intelligence layer: image processing, crop health analysis, organic treatment recommendations, and real-time field dashboards — all trained on local conditions.

---

## Markets

| Region | Status | Crops | Farms (Y1) | Primary channel |
|--------|--------|-------|-----------|-----------------|
| 🇲🇽 **Jalisco, Mexico** | Production | Maiz, agave, berries, aguacate, cana, chile | 20 | WhatsApp (Spanish) |
| 🇨🇦 **Ontario, Canada** | Pilot | Corn, soy, wheat, apple, grape, greenhouse | 3 demo | SMS (bilingual) |

The platform is region-aware at every layer — phenology calendars, disease libraries, ancestral/traditional methods, fertilizer recommendations, and cost estimates switch based on farm location (state + country).

---

## The Thesis

Farmers don't need to be convinced of regenerative practices philosophically — they need yield data and income math that makes it the rational choice. cultivOS makes that math visible: in WhatsApp, in plain Spanish, with color instead of numbers.

> *"El suelo que cuidas hoy alimenta a tus nietos mañana."*

---

## What's Built

**2539 tests · 50 API modules · 64 frontend pages · 8 demo farms across 2 countries**

### Intelligence Layer ("Cerebro")

| Module | What it does |
|--------|-------------|
| **Health scoring** | Composite 0-100 score from NDVI + soil + thermal + trend + microbiome |
| **NDVI processing** | Multispectral band math → vegetation index → zone classification |
| **Thermal stress** | Water stress map + irrigation deficit detection from drone thermal imagery |
| **Disease/pest detection** | NDVI anomaly patterns classified as disease vs pest vs nutrient deficiency |
| **Crop photo analysis** | Upload field photos for instant visual classification |
| **Growth stage tracking** | Phenology-aware development monitoring |
| **Anomaly detection** | Statistical outliers flagged across time series |
| **Data fusion** | Multi-sensor health synthesis with confidence scores |

### Recommendation Engine

| Module | What it does |
|--------|-------------|
| **Treatment recommendations** | Organic-only, region-aware, cost in MXN or CAD per hectare |
| **Soil amendment calculator** | Prescribes composta, cal, azufre, etc. from soil test values |
| **Crop rotation planner** | Multi-year plan based on last crop, regional seasons, soil health |
| **Irrigation optimizer** | 7-day water schedule from weather + soil + thermal |
| **Yield prediction** | SIAP baselines (MX) + OMAFRA baselines (ON), health-adjusted with confidence ranges |
| **Intervention scoring** | Cost-benefit ranking of available treatments |
| **Regenerative scorecard** | 12-point assessment of regenerative practice adoption |
| **Carbon MRV** | Soil carbon measurement, reporting, verification |

### Knowledge Base

| Module | What it does |
|--------|-------------|
| **Fertilizers** | 13 organic methods (composta, bocashi, biochar, cover crops, wood ash, cattle manure…) |
| **Ancestral methods** | 12 traditional practices — 8 Mesoamerican (milpa, chinampa, terrazas) + 4 Ontario (cover cropping, corn-soy-wheat rotation, windbreaks, companion planting) |
| **Crop database** | 17 crops across Mexico + Canada with growing seasons, companions, optimal temps |
| **Disease library** | 15 diseases with organic treatment protocols — regionally tagged |
| **Regional profiles** | Climate zone, soil type, growing season, currency, seasonal notes per region |
| **Seasonal calendar** | Phenology-based alerts (preparacion/siembra/cosecha/mantenimiento/frost_warning) |

### Farmer-Facing

| Module | What it does |
|--------|-------------|
| **Farm dashboard** | Spanish-first, mobile-friendly, color-coded health indicators |
| **Field detail page** | Full Cerebro drill-down per field |
| **Treatment timeline** | Before/after health score delta per intervention |
| **WhatsApp/SMS alerts** | Dedup'd notifications with alert config per farm |
| **Cooperative management** | Farmer group CRUD with aggregate dashboards |
| **Farmer feedback** | Treatment trust scores from end-user ratings |
| **Photo uploads** | Field photo log with ML classification |

### Admin & Investor

| Module | What it does |
|--------|-------------|
| **Intel dashboard** | Dark-theme admin view with cross-farm analytics |
| **Executive dashboard** | Platform-wide KPIs at `/ejecutivo` for grant reviewers |
| **Cerebro analytics** | AI decision log, accuracy tracking, activity trends |
| **Prediction accuracy (MAPE)** | AI self-validation at `/precision-ia` — per-field and aggregate |
| **Treatment effectiveness by crop** | Ranking by mean health delta |
| **Farmer impact summary** | Per-farm improvement journey metrics |
| **Portfolio report** | Multi-farm PDF for investors and loans |
| **FODECIJAL report** | Grant-specific scientific rigor narrative |
| **Economic impact** | ROI, payback, water/fertilizer savings per intervention |
| **Regional intelligence** | Cross-farm aggregation by municipality and crop |

### Operations

| Module | What it does |
|--------|-------------|
| **Drone mission planning** | Boustrophedon waypoints from field boundary polygons |
| **Flight log tracking** | Per-flight metadata, coverage, battery, outputs |
| **Weather integration** | OpenWeatherMap forecasts + severe weather alerts |
| **Soil microbiome** | Microbial diversity tracking with auto-classification |
| **CSV import/export** | Bulk soil data import, Spanish-header farm export |
| **PDF reports** | Spanish-language farm reports for FIRA loans |
| **Role-based auth** | JWT with admin / researcher / farmer roles |
| **System health** | Live API health dashboard for ops monitoring |

---

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy / Pydantic v2
- **Frontend**: Vanilla HTML/CSS/JS (no build step) + Chart.js
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Processing**: NumPy (NDVI band math, thermal analysis)
- **Weather**: OpenWeatherMap API (global, lat/lon-based)
- **Auth**: JWT with role-based access
- **Testing**: pytest (2539 tests, region-parameterized fixtures)

---

## Run

```bash
./run.sh
# → http://localhost:8000              Farm dashboard
# → http://localhost:8000/intel        Intelligence dashboard
# → http://localhost:8000/ejecutivo    Executive dashboard (investor KPIs)
# → http://localhost:8000/demo         Guided platform walkthrough
# → http://localhost:8000/cerebro      Cerebro AI analytics
```

Or manually:
```bash
PYTHONPATH="$PWD/src" uvicorn cultivos.app:create_app --factory --port 8000
```

Seed the demo database (5 Jalisco farms + 3 Ontario farms, 6 months of time-series data):
```bash
PYTHONPATH="$PWD/src" python3 scripts/seed_demo.py
```

---

## Test

```bash
PYTHONPATH="$PWD/src" pytest tests/ -q               # Full suite (2539 tests, ~3 min)
PYTHONPATH="$PWD/src" pytest tests/test_ontario.py   # Ontario expansion only
PYTHONPATH="$PWD/src" pytest tests/ -k "recommend"   # Recommendation engine
```

---

## Architecture

```
src/cultivos/
├── app.py                   # FastAPI factory (50 routers registered)
├── config.py                # Pydantic settings from .env
├── auth.py                  # JWT + role-based access
├── middleware.py            # Error handling
├── api/                     # 50 route modules (thin — HTTP only)
├── services/
│   ├── crop/                # ndvi, thermal, health, disease, phenology
│   ├── intelligence/        # recommendations, rotation, irrigation,
│   │                        # regions, seasonal_calendar, economics,
│   │                        # carbon, yield_model, regenerative
│   ├── drone/               # mission planning
│   ├── alerts/              # SMS/WhatsApp dispatch with dedup
│   ├── pipeline/            # CSV ingest
│   └── weather_client.py    # OpenWeatherMap wrapper
├── models/                  # 30+ Pydantic schemas
└── db/                      # SQLAlchemy ORM + session + seeds

frontend/                    # 64 HTML pages (vanilla JS, no build)
├── index.html               # Farm dashboard
├── field.html               # Field Cerebro drill-down
├── intel.html               # Intelligence dashboard
├── ejecutivo.html           # Executive KPIs
├── cerebro-analytics.html   # AI decision log
├── precision-ia.html        # MAPE accuracy tracker
├── fotos.html               # Field photo upload
├── cooperativa.html         # Cooperative management
├── calculadora-suelo.html   # Soil amendment calculator
└── … 55 more
```

### Region-Aware Design

The platform supports multi-country operations via a clean abstraction:

```python
# src/cultivos/services/intelligence/regions.py
PROFILES = {
    "jalisco_mx": RegionProfile(climate="tropical_subtropical",
                                soil="andosoles volcanicos",
                                currency="MXN",
                                key_crops=["maiz", "agave", "berries"]),
    "ontario_ca": RegionProfile(climate="temperate_continental",
                                soil="glacial till",
                                currency="CAD",
                                key_crops=["corn", "soy", "wheat", "apple", "grape"]),
}
```

Seasonal calendars, recommendation engines, and knowledge queries all accept a `region` parameter. Default behavior (`region="jalisco"`) preserves backward compatibility — adding Canada didn't break a single existing Jalisco test.

---

## Key Metrics (targets)

- **15–25% input cost reduction** per farm (aligned with MDPI 2025 meta-analysis of 85 precision-ag studies)
- **85 farms by Year 3, 170 by Year 5**
- **57% water wasted** by irrigation inefficiency in Mexican agriculture (CONAGUA 2017–2018) — we close this gap
- **~0% precision ag adoption** on small farms in Mexico (FAO) — our TAM

---

## Team

- **Sebastian Sanchez Garcia** — CEO / Co-founder. Guadalajara-born, Toronto-based.
- **Mubeen Zulfiqar** — CTO / Co-founder. MSc CS Waterloo.
- **Arshia Heravi** — Software Engineer / Co-founder. Creator of AutoAgent.

## Partnerships

- **ITESO** (Guadalajara) — Academic validation partner. Drone lab + campus garden.

## Funding

- **FODECIJAL 2026** — $2M MXN applied (Cerebro AI validation, deadline May 14, 2026)
- **Impulsora de Innovación** — $6M MXN target (hardware + operations)

---

## Roadmap

| Year | Stage | Corridor | Farms | Revenue (MXN) |
|------|-------|----------|-------|---------------|
| Y1 | Launch | Valles Centrales de Jalisco | 20 | $2.6M |
| Y2 | Growth | Deeper Jalisco penetration | 45 | $6.0M |
| Y3 | Scale | + Altos de Jalisco + **Ontario pilot** | 75 | $10.1M |
| Y4 | Regional | + Costa Sur + aguacate zone | 110 | $15.0M |
| Y5 | Leader | Full Jalisco + **Ontario operational** | 170 | $24.0M |

### Beyond agriculture (same drone fleet, new markets)
- **Humanitarian**: water delivery to marginalized communities
- **Emergency**: wildfire detection + thermal imaging
- **Environmental**: water quality, reforestation monitoring
- **Commercial**: solar panel and building inspection
- **Construction**: progress monitoring, volumetric measurements

---

## License

Proprietary — CultivOS Mexico S.A. de C.V. All rights reserved.

**Website**: [cultivosagro.com](https://cultivosagro.com)
**Contact**: partnership, investment, and pilot inquiries welcome.
