# CLAUDE.md — cultivOS Project Instructions

## What is this project?

cultivOS is the brain of precision agriculture — an AI-powered platform that transforms drone imagery (NDVI, thermal) into actionable farm intelligence for small and medium farms. Starting in Jalisco, Mexico, expanding to Ontario, Canada.

**Not a drone company.** We use third-party hardware (DJI). Our value is the intelligence layer: image processing, crop health analysis, agronomic recommendations, and real-time field dashboards — all trained on local conditions.

**Owner**: Seb (SebSanGar) — based in Toronto, ADHD, prefers concise visual explanations
**Markets**: Jalisco, Mexico (primary) + Ontario, Canada (expansion)
**Language**: Spanish-first (farmer-facing), English (codebase + docs)

## Key metrics

- $414,000 MXN saved per farm/year
- 85 farms by Year 3, 170 by Year 5
- 57% water wasted by inefficiency (CONAGUA) — we fix this
- 84% of Jalisco municipalities in drought (2024)
- <5% of small farms have access to precision agriculture

## Architecture

```
frontend/              → Dashboard (served on :3000)
  index.html           → Farm dashboard, health maps, alerts
  styles.css           → Dark/light theme, agricultural aesthetic
  app.js               → All frontend logic, map rendering, charts

src/cultivos/          → FastAPI backend (served on :8000)
  api/
    farms.py           → Farm CRUD, health endpoints
    flights.py         → Drone mission planning, flight logs
    analysis.py        → NDVI/thermal analysis endpoints
    alerts.py          → WhatsApp/SMS alert management
    dashboard.py       → Aggregated farm intelligence
  services/
    crop/
      ndvi.py          → NDVI image processing pipeline
      thermal.py       → Thermal stress detection
      health.py        → Crop health scoring engine
      disease.py       → Disease/pest identification
    drone/
      mission.py       → Flight path optimization
      fleet.py         → Drone status, battery, maintenance
      compliance.py    → AFAC regulations, no-fly zones
    pipeline/
      ingest.py        → Image upload, georeferencing
      process.py       → NDVI/thermal computation
      storage.py       → Processed data storage
    intelligence/
      recommendations.py → Organic treatment recommendations
      irrigation.py     → Water optimization
      rotation.py       → Crop rotation planning
      yield.py          → Yield prediction models
    alerts/
      whatsapp.py      → WhatsApp Business API integration
      sms.py           → SMS fallback
      scheduler.py     → Alert timing and frequency
  models/
    farm.py            → Farm, Field, Crop models
    flight.py          → Mission, FlightLog models
    analysis.py        → NDVIResult, ThermalResult, HealthScore
    alert.py           → Alert, AlertRule models
  db/
    models.py          → SQLAlchemy ORM
    session.py         → Database session management
  utils/
    geo.py             → GPS, coordinate transforms, area calculations
    weather.py         → Weather API integration
    units.py           → Hectare/acre conversion, MXN/CAD

tests/                 → pytest test suite
docs/                  → API docs, agronomic references
scripts/               → Deployment, data migration
```

## Hardware fleet

| Drone | Purpose | Cost (MXN) |
|-------|---------|------------|
| DJI Mavic 3 Multispectral | NDVI mapping (4 bands + RGB), 200 ha/flight | $106,000 |
| DJI Mavic 3 Thermal | Thermal stress detection, 640x512 sensor | $130,000 |
| DJI Agras T100 | Precision spraying, 100L tank, 25 ha/hr, LiDAR | $771,000 |

4 batteries + 8-9 min charge = 10-12 productive hours/day

## Key conventions

- **Backend**: snake_case (Python standard)
- **Frontend**: camelCase (JavaScript standard)
- **API responses**: snake_case (Pydantic models)
- **User-facing text**: Spanish (farmer-facing), English (admin/dev)
- **Units**: Hectares (not acres), MXN (primary), CAD (Ontario)
- **No emojis in code or UI** (except flag emojis for market toggle)
- **Services don't import routes. Routes import services.** One-way dependency.
- **All image processing functions**: pure — arrays in, results out. No HTTP, no side effects.

## Environment variables (.env)

```
# Database
DB_URL=sqlite:///cultivos.db

# WhatsApp Business API
WHATSAPP_API_TOKEN=...
WHATSAPP_PHONE_ID=...

# Weather API
OPENWEATHER_API_KEY=...

# Storage (S3-compatible for drone imagery)
S3_BUCKET=cultivos-imagery
S3_ENDPOINT=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Optional
ANTHROPIC_API_KEY=...      # AI-powered recommendations
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

## How to run

```bash
# Terminal 1 — Backend
cd ~/Documents/cultivOS
./run.sh

# Or manually:
uvicorn src.cultivos.api:create_app --factory --reload --port 8000
```

## Expansion corridors (Year 1-5)

1. Valles Centrales de Jalisco (Y1-Y2)
2. Altos de Jalisco (Y3)
3. Costa Sur y Zona de Cultivo de Aguacate (Y4-Y5)
4. Ontario, Canada (Y3+)

## Beyond agriculture (same infrastructure)

- Humanitarian: water delivery to marginalized communities
- Emergency: wildfire detection, thermal + water drops
- Environmental: water quality, reforestation monitoring
- Commercial: solar panel inspection, building inspection
- Construction: progress monitoring, volumetric measurements
