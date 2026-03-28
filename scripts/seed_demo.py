"""
Demo data seeder for cultivOS — populates the DB with realistic Jalisco farm data.

Usage:
    PYTHONPATH=src python3 scripts/seed_demo.py

Creates 3 farms with 2-3 fields each, plus historical NDVI, soil, thermal,
health scores, treatments, and weather records showing improvement over 3 months.
Idempotent: checks for existing demo data before inserting.
"""

from datetime import datetime, timedelta

from cultivos.db.models import (
    Farm, Field, HealthScore, NDVIResult, SoilAnalysis,
    ThermalResult, TreatmentRecord, WeatherRecord,
)

DEMO_MARKER = "[DEMO]"


def _demo_exists(session) -> bool:
    """Check if demo data is already seeded."""
    farm = session.query(Farm).filter(Farm.name.like(f"%{DEMO_MARKER}%")).first()
    return farm is not None


def seed_demo_data(session):
    """Seed the database with realistic Jalisco demo data. Idempotent."""
    if _demo_exists(session):
        return

    now = datetime.utcnow()
    three_months_ago = now - timedelta(days=90)

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
        session.flush()  # get farm.id

        for field_data in fields_data:
            field = Field(farm_id=farm.id, **field_data)
            session.add(field)
            session.flush()  # get field.id

            _seed_field_history(session, farm, field, now, three_months_ago)

    session.commit()


def _seed_field_history(session, farm, field, now, start_date):
    """Seed historical records for a single field showing improvement over time."""
    # Generate 6 time points over 3 months
    intervals = 6
    delta = (now - start_date) / intervals

    # Base values that improve over time
    base_ndvi = 0.35 + (hash(field.name) % 10) * 0.02  # 0.35-0.53 starting
    base_health = 40 + (hash(field.name) % 15)  # 40-54 starting
    base_temp = 28.0 + (hash(field.name) % 8)  # 28-35 starting stress

    for i in range(intervals):
        ts = start_date + delta * i
        improvement = i * 0.04  # progressive improvement

        # NDVI — improving over time
        ndvi_mean = min(base_ndvi + improvement, 0.85)
        ndvi_std = 0.08 - i * 0.005  # less variance as field improves
        session.add(NDVIResult(
            field_id=field.id,
            ndvi_mean=round(ndvi_mean, 3),
            ndvi_std=round(max(ndvi_std, 0.02), 3),
            ndvi_min=round(max(ndvi_mean - 0.15, 0.05), 3),
            ndvi_max=round(min(ndvi_mean + 0.15, 0.95), 3),
            pixels_total=50000,
            stress_pct=round(max(30 - i * 5, 2), 1),
            zones=[
                {"zone": "norte", "ndvi_mean": round(ndvi_mean + 0.02, 3)},
                {"zone": "sur", "ndvi_mean": round(ndvi_mean - 0.02, 3)},
            ],
            analyzed_at=ts,
        ))

        # Health scores — improving
        health = min(base_health + i * 8, 92)
        trend = "improving" if i > 0 else "stable"
        session.add(HealthScore(
            field_id=field.id,
            score=round(health, 1),
            ndvi_mean=round(ndvi_mean, 3),
            ndvi_std=round(max(ndvi_std, 0.02), 3),
            stress_pct=round(max(30 - i * 5, 2), 1),
            trend=trend,
            sources=["ndvi", "soil"],
            breakdown={"ndvi": round(ndvi_mean * 100, 1), "soil": round(health * 0.9, 1)},
            scored_at=ts,
        ))

        # Thermal — stress reducing over time
        temp_mean = base_temp - i * 0.5
        session.add(ThermalResult(
            field_id=field.id,
            temp_mean=round(temp_mean, 1),
            temp_std=2.5,
            temp_min=round(temp_mean - 4, 1),
            temp_max=round(temp_mean + 6, 1),
            pixels_total=40000,
            stress_pct=round(max(25 - i * 4, 3), 1),
            irrigation_deficit=i < 2,  # deficit only early on
            analyzed_at=ts,
        ))

    # Soil analysis — 2 samples (before and after treatments)
    session.add(SoilAnalysis(
        field_id=field.id,
        ph=6.2, organic_matter_pct=2.1, nitrogen_ppm=25, phosphorus_ppm=15,
        potassium_ppm=120, texture="loam", moisture_pct=22, electrical_conductivity=0.8,
        depth_cm=30, notes="Muestra inicial", sampled_at=start_date,
    ))
    session.add(SoilAnalysis(
        field_id=field.id,
        ph=6.5, organic_matter_pct=3.0, nitrogen_ppm=35, phosphorus_ppm=20,
        potassium_ppm=140, texture="loam", moisture_pct=28, electrical_conductivity=0.6,
        depth_cm=30, notes="Post-tratamiento organico", sampled_at=now - timedelta(days=15),
    ))

    # Treatments — 2 organic treatments
    session.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=base_health,
        problema="Estres hidrico moderado",
        causa_probable="Riego insuficiente y suelo compactado",
        tratamiento="Aplicar acolchado organico (mulch) de 10cm y ajustar frecuencia de riego",
        costo_estimado_mxn=3500,
        urgencia="alta",
        prevencion="Monitoreo semanal de humedad del suelo con sensor capacitivo",
        organic=True,
        ancestral_method_name="Acolchado con rastrojo",
        applied_at=start_date + timedelta(days=20),
        applied_notes="Aplicado con rastrojo de maiz",
        created_at=start_date + timedelta(days=10),
    ))
    session.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=base_health + 16,
        problema="Materia organica baja",
        causa_probable="Suelo degradado por monocultivo previo",
        tratamiento="Incorporar composta madura 5 ton/ha + inoculante micorriza",
        costo_estimado_mxn=5000,
        urgencia="media",
        prevencion="Rotacion con leguminosas cada 2 ciclos",
        organic=True,
        applied_at=start_date + timedelta(days=50),
        applied_notes="Composta de lombriz local",
        created_at=start_date + timedelta(days=40),
    ))

    # Weather — 3 records spread across the period
    for j, offset_days in enumerate([0, 30, 60]):
        ts = start_date + timedelta(days=offset_days)
        session.add(WeatherRecord(
            farm_id=farm.id,
            temp_c=round(24 + j * 2, 1),
            humidity_pct=round(55 + j * 5, 1),
            wind_kmh=round(12 - j, 1),
            rainfall_mm=round(j * 8.5, 1),
            description="Parcialmente nublado" if j < 2 else "Lluvia ligera",
            forecast_3day=[
                {"day": 1, "temp_c": 25, "rain_mm": 0},
                {"day": 2, "temp_c": 26, "rain_mm": 5},
                {"day": 3, "temp_c": 24, "rain_mm": 12},
            ],
            recorded_at=ts,
        ))


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
