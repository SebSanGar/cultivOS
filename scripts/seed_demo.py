"""
Demo data seeder for cultivOS — populates the DB with realistic Jalisco farm data.

Usage:
    PYTHONPATH=src python3 scripts/seed_demo.py

Creates 3 farms with 2-3 fields each, plus 6 months of time-series data:
weekly NDVI/health, bi-weekly thermal, monthly soil, every-other-day weather,
and 4 treatments per field showing a clear regenerative improvement arc.
Idempotent: checks for existing demo data before inserting.
"""

import math
from datetime import datetime, timedelta

from cultivos.db.models import (
    Farm, Field, HealthScore, NDVIResult, SoilAnalysis,
    ThermalResult, TreatmentRecord, WeatherRecord,
)

DEMO_MARKER = "[DEMO]"

# Jalisco seasons: temporal (rainy) June-October, secas (dry) November-May
TEMPORAL_MONTHS = {6, 7, 8, 9, 10}


def _demo_exists(session) -> bool:
    """Check if demo data is already seeded."""
    farm = session.query(Farm).filter(Farm.name.like(f"%{DEMO_MARKER}%")).first()
    return farm is not None


def _seasonal_modifier(dt):
    """Return a modifier based on Jalisco season. Temporal (rainy) is better for crops."""
    if dt.month in TEMPORAL_MONTHS:
        return 0.08  # rainy season boost
    return -0.03  # dry season slight penalty


def seed_demo_data(session):
    """Seed the database with realistic Jalisco demo data. Idempotent."""
    if _demo_exists(session):
        return

    now = datetime.utcnow()
    six_months_ago = now - timedelta(days=182)

    # --- Farms ---
    farms_data = [
        {
            "name": f"Rancho Azul {DEMO_MARKER}",
            "owner_name": "Carlos Hernandez",
            "location_lat": 20.8833,
            "location_lon": -103.8333,
            "total_hectares": 45.0,
            "municipality": "Tequila",
            "state": "Jalisco",
            "fields": [
                {"name": "Agave Azul Norte", "crop_type": "agave", "hectares": 20.0,
                 "planted_at": now - timedelta(days=730)},
                {"name": "Agave Azul Sur", "crop_type": "agave", "hectares": 15.0,
                 "planted_at": now - timedelta(days=540)},
                {"name": "Maiz Temporal", "crop_type": "maiz", "hectares": 10.0,
                 "planted_at": now - timedelta(days=120)},
            ],
        },
        {
            "name": f"Berries del Valle {DEMO_MARKER}",
            "owner_name": "Maria Lopez Gutierrez",
            "location_lat": 20.6736,
            "location_lon": -103.3920,
            "total_hectares": 30.0,
            "municipality": "Zapopan",
            "state": "Jalisco",
            "fields": [
                {"name": "Fresa Invernadero A", "crop_type": "fresa", "hectares": 8.0,
                 "planted_at": now - timedelta(days=90)},
                {"name": "Arandano Seccion 1", "crop_type": "arandano", "hectares": 12.0,
                 "planted_at": now - timedelta(days=180)},
                {"name": "Frambuesa Piloto", "crop_type": "frambuesa", "hectares": 10.0,
                 "planted_at": now - timedelta(days=60)},
            ],
        },
        {
            "name": f"Milpa Tradicional Autlan {DEMO_MARKER}",
            "owner_name": "Don Jose Martinez",
            "location_lat": 19.7714,
            "location_lon": -104.3625,
            "total_hectares": 25.0,
            "municipality": "Autlan de Navarro",
            "state": "Jalisco",
            "fields": [
                {"name": "Milpa Principal", "crop_type": "maiz", "hectares": 15.0,
                 "planted_at": now - timedelta(days=100)},
                {"name": "Frijol y Calabaza", "crop_type": "frijol", "hectares": 10.0,
                 "planted_at": now - timedelta(days=95)},
            ],
        },
    ]

    for farm_data in farms_data:
        fields_data = farm_data.pop("fields")
        farm = Farm(**farm_data)
        session.add(farm)
        session.flush()

        for field_data in fields_data:
            field = Field(farm_id=farm.id, **field_data)
            session.add(field)
            session.flush()

            _seed_field_history(session, farm, field, now, six_months_ago)

        _seed_weather_history(session, farm, now, six_months_ago)

    session.commit()


def _seed_field_history(session, farm, field, now, start_date):
    """Seed 6 months of time-series data for a single field.

    Data shows a clear before-regenerative → after-regenerative improvement arc:
    - Weeks 1-8: degraded baseline (low NDVI, low health, high stress)
    - Weeks 9-12: first treatments applied, early recovery
    - Weeks 13-26: sustained improvement, strong health scores
    """
    total_days = (now - start_date).days  # ~182
    total_weeks = total_days // 7  # ~26

    # Per-field variation from field name hash
    field_hash = hash(field.name) % 100
    base_ndvi = 0.30 + (field_hash % 12) * 0.01  # 0.30-0.41
    base_health = 35 + (field_hash % 12)  # 35-46
    base_temp = 30.0 + (field_hash % 6)  # 30-35 starting stress

    # --- Weekly NDVI + Health Scores (26 records each) ---
    for week in range(total_weeks):
        ts = start_date + timedelta(weeks=week)
        progress = week / max(total_weeks - 1, 1)  # 0.0 → 1.0
        seasonal = _seasonal_modifier(ts)

        # Improvement curve: slow start, accelerates after treatments (week 8-10)
        if week < 8:
            improvement = progress * 0.05
        elif week < 14:
            improvement = 0.05 + (week - 8) * 0.03
        else:
            improvement = 0.05 + 6 * 0.03 + (week - 14) * 0.015

        ndvi_mean = min(base_ndvi + improvement + seasonal, 0.88)
        ndvi_std = max(0.10 - progress * 0.06, 0.02)

        session.add(NDVIResult(
            field_id=field.id,
            ndvi_mean=round(ndvi_mean, 3),
            ndvi_std=round(ndvi_std, 3),
            ndvi_min=round(max(ndvi_mean - 0.15, 0.05), 3),
            ndvi_max=round(min(ndvi_mean + 0.12, 0.95), 3),
            pixels_total=50000,
            stress_pct=round(max(35 - week * 1.4, 2), 1),
            zones=[
                {"zone": "norte", "ndvi_mean": round(ndvi_mean + 0.02, 3)},
                {"zone": "sur", "ndvi_mean": round(ndvi_mean - 0.02, 3)},
            ],
            analyzed_at=ts,
        ))

        health = min(base_health + improvement * 150, 94)
        if week < 2:
            trend = "stable"
        elif week < 8:
            trend = "stable"
        else:
            trend = "improving"

        session.add(HealthScore(
            field_id=field.id,
            score=round(health, 1),
            ndvi_mean=round(ndvi_mean, 3),
            ndvi_std=round(ndvi_std, 3),
            stress_pct=round(max(35 - week * 1.4, 2), 1),
            trend=trend,
            sources=["ndvi", "soil", "thermal"],
            breakdown={
                "ndvi": round(ndvi_mean * 100, 1),
                "soil": round(health * 0.85, 1),
                "thermal": round(max(60 - week * 1.5, 20), 1),
            },
            scored_at=ts,
        ))

    # --- Bi-weekly Thermal (13 records) ---
    for bi_week in range(total_weeks // 2):
        ts = start_date + timedelta(weeks=bi_week * 2)
        progress = bi_week / max(total_weeks // 2 - 1, 1)

        temp_mean = base_temp - progress * 5
        session.add(ThermalResult(
            field_id=field.id,
            temp_mean=round(temp_mean, 1),
            temp_std=2.5,
            temp_min=round(temp_mean - 4, 1),
            temp_max=round(temp_mean + 6, 1),
            pixels_total=40000,
            stress_pct=round(max(30 - bi_week * 2.5, 3), 1),
            irrigation_deficit=bi_week < 4,
            analyzed_at=ts,
        ))

    # --- Monthly Soil (6 records) ---
    for month_idx in range(6):
        ts = start_date + timedelta(days=month_idx * 30)
        progress = month_idx / 5.0

        # Soil improves gradually with organic amendments
        ph = round(6.0 + progress * 0.5, 1)
        om = round(1.8 + progress * 1.4, 1)  # organic matter 1.8% → 3.2%
        n = round(20 + progress * 20, 0)  # nitrogen 20 → 40 ppm
        p = round(12 + progress * 10, 0)
        k = round(110 + progress * 40, 0)
        moisture = round(18 + progress * 12, 0)
        ec = round(0.9 - progress * 0.3, 1)

        notes_map = {
            0: "Muestra inicial — suelo degradado por monocultivo previo",
            1: "Post primera aplicacion de composta",
            2: "Incorporacion de abonos verdes",
            3: "Post inoculacion micorriza",
            4: "Suelo en recuperacion activa",
            5: "Muestra final — mejora significativa en materia organica",
        }

        session.add(SoilAnalysis(
            field_id=field.id,
            ph=ph,
            organic_matter_pct=om,
            nitrogen_ppm=n,
            phosphorus_ppm=p,
            potassium_ppm=k,
            texture="loam",
            moisture_pct=moisture,
            electrical_conductivity=ec,
            depth_cm=30,
            notes=notes_map[month_idx],
            sampled_at=ts,
        ))

    # --- 4 Treatments at intervals ---
    treatments = [
        {
            "offset_days": 14,
            "health_offset": 0,
            "problema": "Suelo compactado y materia organica baja",
            "causa_probable": "Monocultivo previo sin rotacion ni enmiendas organicas",
            "tratamiento": "Aplicar composta madura 8 ton/ha + acolchado organico (mulch) de 10cm",
            "costo_estimado_mxn": 4500,
            "urgencia": "alta",
            "prevencion": "Rotacion con leguminosas cada 2 ciclos + incorporar rastrojo",
            "ancestral_method_name": "Acolchado con rastrojo",
            "applied_notes": "Composta de lombriz local + rastrojo de maiz como mulch",
        },
        {
            "offset_days": 50,
            "health_offset": 10,
            "problema": "Baja actividad microbiana en rizosfera",
            "causa_probable": "pH acido y ausencia de inoculantes biologicos",
            "tratamiento": "Inocular con micorriza arbuscular 2kg/ha + te de composta semanal",
            "costo_estimado_mxn": 3200,
            "urgencia": "media",
            "prevencion": "Mantener cobertura vegetal permanente para alimentar microbiota",
            "ancestral_method_name": "Abonos verdes",
            "applied_notes": "Inoculante Glomus intraradices + te de composta aerobico",
        },
        {
            "offset_days": 95,
            "health_offset": 25,
            "problema": "Estres hidrico moderado en zona sur del campo",
            "causa_probable": "Distribucion irregular de riego y suelo con baja retencion",
            "tratamiento": "Instalar riego por goteo + biochar 3 ton/ha para retencion hidrica",
            "costo_estimado_mxn": 8500,
            "urgencia": "media",
            "prevencion": "Monitoreo semanal de humedad con sensor capacitivo",
            "applied_notes": "Biochar de cascara de coco + goteo cada 50cm",
        },
        {
            "offset_days": 140,
            "health_offset": 40,
            "problema": "Deficiencia leve de nitrogeno en fase de crecimiento",
            "causa_probable": "Alta demanda del cultivo + lixiviacion por lluvias temporales",
            "tratamiento": "Aplicar bocashi 4 ton/ha + siembra de frijol de abono intercalado",
            "costo_estimado_mxn": 3000,
            "urgencia": "baja",
            "prevencion": "Intercalar leguminosas fijadoras de nitrogeno en rotacion",
            "ancestral_method_name": "Milpa",
            "applied_notes": "Bocashi fermentado 14 dias + frijol terciopelo como cobertura",
        },
    ]

    for t in treatments:
        offset = t.pop("offset_days")
        health_offset = t.pop("health_offset")
        session.add(TreatmentRecord(
            field_id=field.id,
            health_score_used=base_health + health_offset,
            organic=True,
            applied_at=start_date + timedelta(days=offset + 10),
            created_at=start_date + timedelta(days=offset),
            **t,
        ))


def _seed_weather_history(session, farm, now, start_date):
    """Seed every-other-day weather records for a farm over 6 months."""
    total_days = (now - start_date).days
    day = 0
    while day < total_days:
        ts = start_date + timedelta(days=day)
        month = ts.month
        is_temporal = month in TEMPORAL_MONTHS

        # Jalisco climate: temporal is warmer/wetter, secas is cooler/drier
        if is_temporal:
            temp = round(26 + (day % 7) * 0.5 + math.sin(day / 30) * 2, 1)
            humidity = round(70 + (day % 5) * 2, 1)
            rainfall = round(max(0, 8 + math.sin(day / 7) * 12), 1)
            description = "Lluvia temporal" if rainfall > 5 else "Parcialmente nublado"
        else:
            temp = round(20 + (day % 7) * 0.5 + math.sin(day / 30) * 2, 1)
            humidity = round(40 + (day % 5) * 2, 1)
            rainfall = round(max(0, math.sin(day / 15) * 3), 1)
            description = "Seco y soleado" if rainfall < 1 else "Llovizna ligera"

        wind = round(10 + math.sin(day / 10) * 5, 1)

        session.add(WeatherRecord(
            farm_id=farm.id,
            temp_c=temp,
            humidity_pct=humidity,
            wind_kmh=wind,
            rainfall_mm=rainfall,
            description=description,
            forecast_3day=[
                {"day": 1, "temp_c": round(temp + 0.5, 1), "rain_mm": round(max(0, rainfall - 2), 1)},
                {"day": 2, "temp_c": round(temp + 1, 1), "rain_mm": round(max(0, rainfall + 3), 1)},
                {"day": 3, "temp_c": round(temp - 0.5, 1), "rain_mm": round(max(0, rainfall - 1), 1)},
            ],
            recorded_at=ts,
        ))

        day += 2  # every other day


if __name__ == "__main__":
    from cultivos.db.session import get_engine
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        seed_demo_data(session)
        farms = session.query(Farm).filter(Farm.name.like(f"%{DEMO_MARKER}%")).count()
        fields = session.query(Field).join(Farm).filter(Farm.name.like(f"%{DEMO_MARKER}%")).count()
        print(f"Demo data seeded: {farms} farms, {fields} fields")
    finally:
        session.close()
