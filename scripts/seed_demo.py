"""
Demo data seeder for cultivOS — populates the DB with realistic Jalisco farm data.

Usage:
    PYTHONPATH=src python3 scripts/seed_demo.py

Creates 5 farms with 2-3 fields each, plus 6 months of time-series data:
weekly NDVI/health, bi-weekly thermal, monthly soil, every-other-day weather,
flight logs per analysis, quarterly microbiome, alerts, farmer feedback,
and 4 treatments per field showing a clear regenerative improvement arc.
Idempotent: checks for existing demo data before inserting.
"""

import math
import random
from datetime import datetime, timedelta

from cultivos.db.models import (
    Alert, AlertConfig, AlertLog, Farm, FarmerFeedback, Field,
    FlightLog, HealthScore, MicrobiomeRecord, NDVIResult, SoilAnalysis,
    ThermalResult, TreatmentRecord, WeatherRecord,
)

DEMO_MARKER = "[DEMO]"

# Jalisco seasons: temporal (rainy) June-October, secas (dry) November-May
TEMPORAL_MONTHS = {6, 7, 8, 9, 10}

# Ontario seasons: growing May-September, winter rest
ONTARIO_GROWING_MONTHS = {5, 6, 7, 8, 9}

# Reproducible randomness for consistent demo data
_rng = random.Random(42)


def _demo_exists(session) -> bool:
    """Check if demo data is already seeded."""
    farm = session.query(Farm).filter(Farm.name.like(f"%{DEMO_MARKER}%")).first()
    return farm is not None


def _seasonal_modifier(dt, region="jalisco"):
    """Return a modifier based on agricultural season. Growing season is better for crops."""
    if region == "ontario":
        if dt.month in ONTARIO_GROWING_MONTHS:
            return 0.08  # growing season boost
        return -0.05  # winter/shoulder penalty
    # Jalisco (default)
    if dt.month in TEMPORAL_MONTHS:
        return 0.08  # rainy season boost
    return -0.03  # dry season slight penalty


def _make_boundary(lat, lon, hectares):
    """Generate a rectangular polygon boundary around a center point.

    Approximates a rectangle of the given area (hectares) centered on (lat, lon).
    At ~20N: 1deg lon ~ 104.5km, 1deg lat ~ 110.6km.
    """
    # hectares to km2
    area_km2 = hectares / 100
    side_km = math.sqrt(area_km2)
    # Convert to degrees
    dlat = side_km / 110.6 / 2
    dlon = side_km / (104.5 * math.cos(math.radians(lat))) / 2
    return [
        [round(lon - dlon, 6), round(lat - dlat, 6)],
        [round(lon + dlon, 6), round(lat - dlat, 6)],
        [round(lon + dlon, 6), round(lat + dlat, 6)],
        [round(lon - dlon, 6), round(lat + dlat, 6)],
        [round(lon - dlon, 6), round(lat - dlat, 6)],  # close polygon
    ]


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
                 "planted_at": now - timedelta(days=730),
                 "offset_lat": 0.003, "offset_lon": 0.001},
                {"name": "Agave Azul Sur", "crop_type": "agave", "hectares": 15.0,
                 "planted_at": now - timedelta(days=540),
                 "offset_lat": -0.003, "offset_lon": 0.001},
                {"name": "Maiz Temporal", "crop_type": "maiz", "hectares": 10.0,
                 "planted_at": now - timedelta(days=120),
                 "offset_lat": 0.0, "offset_lon": -0.004},
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
                 "planted_at": now - timedelta(days=90),
                 "offset_lat": 0.002, "offset_lon": 0.0},
                {"name": "Arandano Seccion 1", "crop_type": "arandano", "hectares": 12.0,
                 "planted_at": now - timedelta(days=180),
                 "offset_lat": -0.002, "offset_lon": 0.002},
                {"name": "Frambuesa Piloto", "crop_type": "frambuesa", "hectares": 10.0,
                 "planted_at": now - timedelta(days=60),
                 "offset_lat": -0.002, "offset_lon": -0.002},
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
                 "planted_at": now - timedelta(days=100),
                 "offset_lat": 0.002, "offset_lon": 0.0},
                {"name": "Frijol y Calabaza", "crop_type": "frijol", "hectares": 10.0,
                 "planted_at": now - timedelta(days=95),
                 "offset_lat": -0.002, "offset_lon": 0.0},
            ],
        },
        {
            "name": f"Agave Los Altos {DEMO_MARKER}",
            "owner_name": "Roberto Sanchez Villarreal",
            "location_lat": 20.7125,
            "location_lon": -102.3481,
            "total_hectares": 60.0,
            "municipality": "Arandas",
            "state": "Jalisco",
            "fields": [
                {"name": "Agave Tequilana Weber", "crop_type": "agave", "hectares": 25.0,
                 "planted_at": now - timedelta(days=900),
                 "offset_lat": 0.003, "offset_lon": 0.002},
                {"name": "Chile de Arbol", "crop_type": "chile", "hectares": 15.0,
                 "planted_at": now - timedelta(days=75),
                 "offset_lat": -0.002, "offset_lon": -0.001},
                {"name": "Jitomate Organico", "crop_type": "jitomate", "hectares": 20.0,
                 "planted_at": now - timedelta(days=45),
                 "offset_lat": 0.0, "offset_lon": -0.004},
            ],
        },
        {
            "name": f"Ganaderia Sustentable Lagos {DEMO_MARKER}",
            "owner_name": "Ana Cristina Ramirez",
            "location_lat": 21.3539,
            "location_lon": -101.9311,
            "total_hectares": 80.0,
            "municipality": "Lagos de Moreno",
            "state": "Jalisco",
            "fields": [
                {"name": "Sorgo Forrajero", "crop_type": "sorgo", "hectares": 30.0,
                 "planted_at": now - timedelta(days=110),
                 "offset_lat": 0.004, "offset_lon": 0.0},
                {"name": "Maiz Grano", "crop_type": "maiz", "hectares": 25.0,
                 "planted_at": now - timedelta(days=100),
                 "offset_lat": -0.003, "offset_lon": 0.003},
                {"name": "Alfalfa Riego", "crop_type": "alfalfa", "hectares": 25.0,
                 "planted_at": now - timedelta(days=200),
                 "offset_lat": -0.003, "offset_lon": -0.003},
            ],
        },
        # --- Ontario / Canada ---
        {
            "name": f"Chatham-Kent Corn & Soy {DEMO_MARKER}",
            "owner_name": "James McAllister",
            "location_lat": 42.4048,
            "location_lon": -82.1819,
            "total_hectares": 140.0,
            "municipality": "Chatham-Kent",
            "state": "Ontario",
            "country": "CA",
            "fields": [
                {"name": "Corn North Field", "crop_type": "corn", "hectares": 80.0,
                 "planted_at": now - timedelta(days=120),
                 "offset_lat": 0.004, "offset_lon": 0.0},
                {"name": "Soybean South Field", "crop_type": "soybean", "hectares": 60.0,
                 "planted_at": now - timedelta(days=110),
                 "offset_lat": -0.004, "offset_lon": 0.0},
            ],
        },
        {
            "name": f"Niagara Orchard & Vineyard {DEMO_MARKER}",
            "owner_name": "Sarah Chen-Williams",
            "location_lat": 43.0896,
            "location_lon": -79.0849,
            "total_hectares": 25.0,
            "municipality": "Niagara-on-the-Lake",
            "state": "Ontario",
            "country": "CA",
            "fields": [
                {"name": "Honeycrisp Block A", "crop_type": "apple", "hectares": 15.0,
                 "planted_at": now - timedelta(days=730),
                 "offset_lat": 0.002, "offset_lon": 0.001},
                {"name": "Riesling Vineyard", "crop_type": "grape", "hectares": 10.0,
                 "planted_at": now - timedelta(days=1095),
                 "offset_lat": -0.002, "offset_lon": -0.001},
            ],
        },
        {
            "name": f"Elgin County Mixed Farm {DEMO_MARKER}",
            "owner_name": "David Fehr",
            "location_lat": 42.7700,
            "location_lon": -81.1000,
            "total_hectares": 42.0,
            "municipality": "Elgin County",
            "state": "Ontario",
            "country": "CA",
            "fields": [
                {"name": "Winter Wheat West", "crop_type": "wheat", "hectares": 40.0,
                 "planted_at": now - timedelta(days=200),
                 "offset_lat": 0.003, "offset_lon": -0.002},
                {"name": "Greenhouse Tomato", "crop_type": "tomato", "hectares": 2.0,
                 "planted_at": now - timedelta(days=60),
                 "offset_lat": -0.001, "offset_lon": 0.001},
            ],
        },
    ]

    all_treatment_ids = []  # collect for farmer feedback later

    for farm_data in farms_data:
        fields_data = farm_data.pop("fields")
        region = "ontario" if farm_data.get("state") == "Ontario" else "jalisco"
        farm = Farm(**farm_data)
        session.add(farm)
        session.flush()

        farm_fields = []
        for field_data in fields_data:
            offset_lat = field_data.pop("offset_lat")
            offset_lon = field_data.pop("offset_lon")
            # Generate boundary polygon
            field_lat = farm.location_lat + offset_lat
            field_lon = farm.location_lon + offset_lon
            field_data["boundary_coordinates"] = _make_boundary(
                field_lat, field_lon, field_data["hectares"])

            field = Field(farm_id=farm.id, **field_data)
            session.add(field)
            session.flush()
            farm_fields.append(field)

            treatment_ids = _seed_field_history(
                session, farm, field, now, six_months_ago, region=region)
            all_treatment_ids.extend(treatment_ids)
            _seed_flight_logs(session, field, now, six_months_ago)
            _seed_microbiome(session, field, now, six_months_ago)

        _seed_weather_history(session, farm, now, six_months_ago, region=region)
        _seed_alerts(session, farm, farm_fields, now, six_months_ago, region=region)
        _seed_alert_config(session, farm)

    # Farmer feedback after all treatments exist
    _seed_farmer_feedback(session, all_treatment_ids)

    session.commit()


def _seed_field_history(session, farm, field, now, start_date, region="jalisco"):
    """Seed 6 months of time-series data for a single field.

    Data shows a clear before-regenerative -> after-regenerative improvement arc:
    - Weeks 1-8: degraded baseline (low NDVI, low health, high stress)
    - Weeks 9-12: first treatments applied, early recovery
    - Weeks 13-26: sustained improvement, strong health scores

    Returns list of treatment record IDs for farmer feedback.
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
        progress = week / max(total_weeks - 1, 1)  # 0.0 -> 1.0
        seasonal = _seasonal_modifier(ts, region=region)

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
        om = round(1.8 + progress * 1.4, 1)  # organic matter 1.8% -> 3.2%
        n = round(20 + progress * 20, 0)  # nitrogen 20 -> 40 ppm
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
    if region == "ontario":
        treatments = [
            {
                "offset_days": 14,
                "health_offset": 0,
                "problema": "Suelo compactado por maquinaria pesada y baja materia organica",
                "causa_probable": "Laboreo convencional en arcillas glaciales y monocultivo maiz-maiz",
                "tratamiento": "Aplicar estiercol composteado 6 ton/ha + sembrar rabano forrajero como descompactador biologico",
                "costo_estimado_mxn": 3600,  # ~270 CAD
                "urgencia": "alta",
                "prevencion": "Rotacion maiz-soya-trigo + cultivos de cobertura invernal cada ano",
                "ancestral_method_name": "Rotacion maiz-soya-trigo",
                "applied_notes": "Estiercol de granja lechera local + rabano forrajero Tillage Radish",
            },
            {
                "offset_days": 50,
                "health_offset": 10,
                "problema": "pH acido (5.5) limitando disponibilidad de nutrientes",
                "causa_probable": "Suelos glaciales naturalmente acidos + lixiviacion por deshielo primaveral",
                "tratamiento": "Aplicar ceniza de madera dura 800 kg/ha + caliza dolomitica 2 ton/ha",
                "costo_estimado_mxn": 2667,  # ~200 CAD
                "urgencia": "media",
                "prevencion": "Monitoreo de pH anual + aplicacion de ceniza cada 3 anos",
                "applied_notes": "Ceniza de arce de aserradero local + caliza de cantera de Guelph",
            },
            {
                "offset_days": 95,
                "health_offset": 25,
                "problema": "Baja actividad biologica del suelo despues de invierno largo",
                "causa_probable": "5 meses de congelamiento reducen poblaciones microbianas activas",
                "tratamiento": "Inocular con micorriza 2 kg/ha en primavera + te de composta cada 2 semanas",
                "costo_estimado_mxn": 4000,  # ~300 CAD
                "urgencia": "media",
                "prevencion": "Mantener cobertura vegetal invernal para alimentar microbiota bajo nieve",
                "ancestral_method_name": "Cover cropping (Ontario)",
                "applied_notes": "Inoculante MycoApply + te de composta de vermicompost",
            },
            {
                "offset_days": 140,
                "health_offset": 40,
                "problema": "Deficiencia de nitrogeno en fase de llenado de grano",
                "causa_probable": "Alta demanda del cultivo + lixiviacion por lluvias de verano",
                "tratamiento": "Aplicar composta 5 ton/ha + planificar cultivo de cobertura de trebol post-cosecha",
                "costo_estimado_mxn": 2400,  # ~180 CAD
                "urgencia": "baja",
                "prevencion": "Incluir soya en rotacion para fijacion biologica de nitrogeno",
                "ancestral_method_name": "Cover cropping (Ontario)",
                "applied_notes": "Composta de granja certificada + semilla de trebol carmin para otono",
            },
        ]
    else:
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

    treatment_ids = []
    for t in treatments:
        offset = t.pop("offset_days")
        health_offset = t.pop("health_offset")
        rec = TreatmentRecord(
            field_id=field.id,
            health_score_used=base_health + health_offset,
            organic=True,
            applied_at=start_date + timedelta(days=offset + 10),
            created_at=start_date + timedelta(days=offset),
            **t,
        )
        session.add(rec)
        session.flush()
        treatment_ids.append((field.id, rec.id))

    return treatment_ids


def _seed_flight_logs(session, field, now, start_date):
    """Seed flight logs matching NDVI and thermal analysis dates.

    Creates 3 flights per field:
    - 2 multispectral health_scan flights (month 1 and month 4)
    - 1 thermal_check flight (month 2)
    """
    flights = [
        {
            "drone_type": "mavic_multispectral",
            "mission_type": "health_scan",
            "flight_date": start_date + timedelta(days=14),
            "duration_minutes": round(25 + field.hectares * 0.8, 1),
            "altitude_m": 50.0,
            "images_count": int(field.hectares * 40),
            "coverage_pct": 98.5,
            "status": "complete",
        },
        {
            "drone_type": "mavic_thermal",
            "mission_type": "thermal_check",
            "flight_date": start_date + timedelta(days=45),
            "duration_minutes": round(20 + field.hectares * 0.6, 1),
            "altitude_m": 40.0,
            "images_count": int(field.hectares * 25),
            "coverage_pct": 95.2,
            "status": "complete",
        },
        {
            "drone_type": "mavic_multispectral",
            "mission_type": "health_scan",
            "flight_date": start_date + timedelta(days=105),
            "duration_minutes": round(25 + field.hectares * 0.8, 1),
            "altitude_m": 50.0,
            "images_count": int(field.hectares * 40),
            "coverage_pct": 99.1,
            "status": "complete",
        },
    ]

    for f in flights:
        session.add(FlightLog(
            field_id=field.id,
            s3_path=f"imagery/demo/{field.farm_id}/{field.id}/{f['flight_date'].strftime('%Y%m%d')}",
            **f,
        ))


def _seed_microbiome(session, field, now, start_date):
    """Seed quarterly microbiome records showing soil biological recovery."""
    # 3 records: baseline (degraded), mid (moderate), current (healthy)
    stages = [
        {
            "offset_days": 10,
            "respiration_rate": 8.5,
            "microbial_biomass_carbon": 120.0,
            "fungi_bacteria_ratio": 0.3,
            "classification": "degraded",
        },
        {
            "offset_days": 90,
            "respiration_rate": 15.2,
            "microbial_biomass_carbon": 280.0,
            "fungi_bacteria_ratio": 0.6,
            "classification": "moderate",
        },
        {
            "offset_days": 170,
            "respiration_rate": 22.8,
            "microbial_biomass_carbon": 450.0,
            "fungi_bacteria_ratio": 1.1,
            "classification": "healthy",
        },
    ]

    for stage in stages:
        offset = stage.pop("offset_days")
        session.add(MicrobiomeRecord(
            field_id=field.id,
            sampled_at=start_date + timedelta(days=offset),
            **stage,
        ))


def _seed_alerts(session, farm, fields, now, start_date, region="jalisco"):
    """Seed alerts and alert logs per farm — shows proactive farmer communication."""
    if region == "ontario":
        alert_templates = [
            {
                "alert_type": "low_health",
                "message": "Salud del campo por debajo del umbral (35/100). Se recomienda inspeccion inmediata.",
                "severity": "critical",
                "offset_days": 7,
            },
            {
                "alert_type": "frost_warning",
                "message": "Pronostico de helada para manana. Proteger plantulas sensibles y cubrir cultivos vulnerables.",
                "severity": "warning",
                "offset_days": 30,
            },
            {
                "alert_type": "pest",
                "message": "Patron de NDVI irregular sugiere posible plaga. Verificar presencia de corn rootworm o soybean aphid.",
                "severity": "warning",
                "offset_days": 55,
            },
            {
                "alert_type": "recommendation",
                "message": "Ventana optima para sembrar cultivo de cobertura. Temperatura del suelo favorable esta semana.",
                "severity": "info",
                "offset_days": 80,
            },
        ]
    else:
        alert_templates = [
            {
                "alert_type": "low_health",
                "message": "Salud del campo por debajo del umbral (35/100). Se recomienda inspeccion inmediata.",
                "severity": "critical",
                "offset_days": 7,
            },
            {
                "alert_type": "irrigation",
                "message": "Deficit hidrico detectado por sensor termico. Programar riego suplementario.",
                "severity": "warning",
                "offset_days": 30,
            },
            {
                "alert_type": "pest",
                "message": "Patron de NDVI irregular sugiere posible plaga. Verificar zona sur del campo.",
                "severity": "warning",
                "offset_days": 55,
            },
            {
                "alert_type": "recommendation",
                "message": "Condiciones optimas para aplicar composta. Temperatura y humedad favorables esta semana.",
                "severity": "info",
                "offset_days": 80,
            },
        ]

    for i, tmpl in enumerate(alert_templates):
        field = fields[i % len(fields)]
        ts = start_date + timedelta(days=tmpl["offset_days"])

        # Alert record (sent via WhatsApp/SMS)
        session.add(Alert(
            farm_id=farm.id,
            field_id=field.id,
            alert_type=tmpl["alert_type"],
            message=tmpl["message"],
            phone_number="+14165551234" if region == "ontario" else "+5213312345678",
            status="sent",
            sent_at=ts,
            created_at=ts,
        ))

        # AlertLog record (internal log)
        session.add(AlertLog(
            farm_id=farm.id,
            field_id=field.id,
            alert_type=tmpl["alert_type"],
            message=tmpl["message"],
            severity=tmpl["severity"],
            acknowledged=i < 2,  # first 2 acknowledged
            created_at=ts,
        ))


def _seed_alert_config(session, farm):
    """Seed alert configuration thresholds per farm."""
    session.add(AlertConfig(
        farm_id=farm.id,
        health_score_floor=40.0,
        ndvi_minimum=0.3,
        temp_max_c=42.0,
    ))


def _seed_farmer_feedback(session, all_treatment_ids):
    """Seed farmer feedback on treatments — powers trust scores page.

    Creates 2 feedback entries per farm (sample from treatments).
    """
    feedback_templates = [
        {
            "rating": 5,
            "worked": True,
            "farmer_notes": "La composta mejoro mucho el suelo. Se nota la diferencia en las plantas.",
        },
        {
            "rating": 4,
            "worked": True,
            "farmer_notes": "El te de composta funciono bien pero tarda en verse el efecto.",
        },
        {
            "rating": 3,
            "worked": False,
            "farmer_notes": "El biochar es caro y no vi cambio rapido. Voy a esperar mas tiempo.",
            "alternative_method": "Mulch de rastrojo de maiz",
        },
        {
            "rating": 5,
            "worked": True,
            "farmer_notes": "El bocashi es excelente. Lo recomiendo a todos mis vecinos.",
        },
        {
            "rating": 4,
            "worked": True,
            "farmer_notes": "La micorriza funciono. Las raices se ven mas fuertes.",
        },
        {
            "rating": 2,
            "worked": False,
            "farmer_notes": "No pude conseguir el inoculante localmente. Use lombricomposta en su lugar.",
            "alternative_method": "Lombricomposta concentrada",
        },
        {
            "rating": 5,
            "worked": True,
            "farmer_notes": "Excelente resultado con la milpa. Frijol fijo el nitrogeno como se dijo.",
        },
        {
            "rating": 4,
            "worked": True,
            "farmer_notes": "El acolchado redujo la evaporacion. Ahorro en riego.",
        },
        {
            "rating": 3,
            "worked": True,
            "farmer_notes": "Funciono parcialmente. Necesito ajustar la dosis para mi tipo de suelo.",
        },
        {
            "rating": 5,
            "worked": True,
            "farmer_notes": "Resultado increible con la rotacion. El maiz rindio 20% mas.",
        },
    ]

    # Use first 10 treatments (or all if fewer), one feedback each
    used = all_treatment_ids[:min(len(all_treatment_ids), len(feedback_templates))]
    for idx, (field_id, treatment_id) in enumerate(used):
        tmpl = feedback_templates[idx]
        session.add(FarmerFeedback(
            field_id=field_id,
            treatment_id=treatment_id,
            **tmpl,
        ))


def _seed_weather_history(session, farm, now, start_date, region="jalisco"):
    """Seed every-other-day weather records for a farm over 6 months."""
    total_days = (now - start_date).days
    day = 0
    while day < total_days:
        ts = start_date + timedelta(days=day)
        month = ts.month

        if region == "ontario":
            is_growing = month in ONTARIO_GROWING_MONTHS
            if is_growing:
                temp = round(20 + (day % 7) * 0.5 + math.sin(day / 30) * 4, 1)
                humidity = round(60 + (day % 5) * 2, 1)
                rainfall = round(max(0, 5 + math.sin(day / 7) * 10), 1)
                description = "Lluvia de verano" if rainfall > 5 else "Parcialmente nublado"
            elif month in (3, 4, 10, 11):
                temp = round(5 + (day % 7) * 0.5 + math.sin(day / 30) * 3, 1)
                humidity = round(55 + (day % 5) * 2, 1)
                rainfall = round(max(0, math.sin(day / 10) * 4), 1)
                description = "Fresco y variable" if rainfall < 2 else "Lluvia ligera"
            else:
                temp = round(-5 + (day % 7) * 0.3 + math.sin(day / 30) * 4, 1)
                humidity = round(70 + (day % 5) * 2, 1)
                rainfall = round(max(0, math.sin(day / 12) * 3), 1)
                description = "Nieve ligera" if temp < -2 else "Nublado y frio"
        else:
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
