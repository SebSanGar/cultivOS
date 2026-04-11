"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/tek-alignment?month=

TEK-sensor alignment: matches AncestralMethod practices for the current month
and field crop_type against live sensor data. sensor_support=True when sensors
confirm the TEK prescription.
"""

from datetime import datetime

from cultivos.db.models import AncestralMethod, Farm, Field, SoilAnalysis, ThermalResult, WeatherRecord


# ── Helpers ────────────────────────────────────────────────────────────────────

def _farm(db):
    f = Farm(name="Finca Test", municipality="Guadalajara", total_hectares=10.0)
    db.add(f)
    db.commit()
    return f


def _field(db, farm_id, crop_type="maiz"):
    f = Field(farm_id=farm_id, name="Lote A", crop_type=crop_type, hectares=5.0)
    db.add(f)
    db.commit()
    return f


def _ancestral(db, name, practice_type, months, crops=None):
    m = AncestralMethod(
        name=name,
        description_es=f"Descripcion de {name}",
        region="jalisco",
        practice_type=practice_type,
        crops=crops or ["maiz"],
        benefits_es="Mejora el suelo",
        problems=["drought"],
        applicable_months=months,
        timing_rationale="Mejor momento del ciclo agricola",
        ecological_benefit=4,
    )
    db.add(m)
    db.commit()
    return m


def _soil_dry(db, field_id):
    """Add low-moisture soil → triggers water stress."""
    db.add(SoilAnalysis(
        field_id=field_id,
        ph=6.5, organic_matter_pct=2.0,
        nitrogen_ppm=20, phosphorus_ppm=15, potassium_ppm=180,
        moisture_pct=15.0,  # < 20% critical
        sampled_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    ))
    db.commit()


def _thermal_stress(db, field_id, stress_pct=60.0):
    """Add high thermal stress."""
    db.add(ThermalResult(
        field_id=field_id,
        temp_mean=38.0, temp_std=3.0, temp_min=30.0, temp_max=45.0,
        pixels_total=1000,
        stress_pct=stress_pct,
        analyzed_at=datetime.utcnow(),
    ))
    db.commit()


def _hot_weather(db, farm_id):
    """Add hot weather record → triggers water stress."""
    db.add(WeatherRecord(
        farm_id=farm_id,
        temp_c=38.0, humidity_pct=20.0, wind_speed_kmh=5.0,
        rainfall_mm=0.0, recorded_at=datetime.utcnow(),
    ))
    db.commit()


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/fields/99999/tek-alignment?month=6")
    assert r.status_code == 404


def test_404_unknown_field(client, db):
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/99999/tek-alignment?month=6")
    assert r.status_code == 404


def test_missing_month_returns_422(client, db):
    farm = _farm(db)
    field = _field(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment")
    assert r.status_code == 422


def test_response_schema_keys(client, db):
    """Response contains all required top-level schema keys."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ancestral(db, "Mulching", "water_management", [6, 7, 8])

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment?month=6")
    assert r.status_code == 200
    data = r.json()
    assert "field_id" in data
    assert "month" in data
    assert "crop_type" in data
    assert "alignment_score_pct" in data
    assert "sensor_context" in data
    assert "practices" in data
    ctx = data["sensor_context"]
    assert "water_stress_level" in ctx
    assert "disease_risk_level" in ctx
    assert "thermal_stress_pct" in ctx


def test_practice_schema_keys(client, db):
    """Each practice entry has required keys."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ancestral(db, "Composicion", "soil_management", [6])

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment?month=6")
    assert r.status_code == 200
    practices = r.json()["practices"]
    assert len(practices) >= 1
    p = practices[0]
    assert "name" in p
    assert "timing_rationale" in p
    assert "sensor_support" in p
    assert "evidence_es" in p


def test_water_management_supported_when_water_stress_present(client, db):
    """Water management TEK practice gets sensor_support=True when water stress is active."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ancestral(db, "Ollas de agua", "water_management", [6])
    _soil_dry(db, field.id)  # triggers water stress urgency

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment?month=6")
    assert r.status_code == 200
    practices = r.json()["practices"]
    water_practice = next((p for p in practices if p["name"] == "Ollas de agua"), None)
    assert water_practice is not None
    assert water_practice["sensor_support"] is True


def test_water_management_not_supported_without_water_stress(client, db):
    """Water management TEK practice gets sensor_support=False when no water stress."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ancestral(db, "Trincheras", "water_management", [6])
    # No dry soil, no hot weather → no water stress

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment?month=6")
    assert r.status_code == 200
    practices = r.json()["practices"]
    p = next((x for x in practices if x["name"] == "Trincheras"), None)
    assert p is not None
    assert p["sensor_support"] is False


def test_no_tek_for_month_returns_empty_practices(client, db):
    """Month with no applicable TEK practices returns empty list and 0% alignment."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ancestral(db, "Siembra de lluvia", "soil_management", [6, 7])  # only Jun-Jul
    _soil_dry(db, field.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment?month=12")
    assert r.status_code == 200
    data = r.json()
    assert data["practices"] == []
    assert data["alignment_score_pct"] == 0


def test_alignment_score_pct_calculation(client, db):
    """alignment_score_pct = (supported / total) * 100, rounded."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _ancestral(db, "Retener agua A", "water_management", [6])
    _ancestral(db, "Retener agua B", "water_management", [6])
    _soil_dry(db, field.id)  # both water methods get support

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment?month=6")
    assert r.status_code == 200
    data = r.json()
    assert data["alignment_score_pct"] == 100.0
    assert all(p["sensor_support"] for p in data["practices"])


def test_crop_type_filter(client, db):
    """Only TEK practices matching field crop_type are included."""
    farm = _farm(db)
    field = _field(db, farm.id, crop_type="agave")
    _ancestral(db, "Milpa maiz", "intercropping", [6], crops=["maiz"])
    _ancestral(db, "Maguey agua", "water_management", [6], crops=["agave"])

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment?month=6")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()["practices"]]
    assert "Maguey agua" in names
    assert "Milpa maiz" not in names


def test_field_crop_type_in_response(client, db):
    """crop_type in response matches the field's crop_type."""
    farm = _farm(db)
    field = _field(db, farm.id, crop_type="chile")

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/tek-alignment?month=6")
    assert r.status_code == 200
    assert r.json()["crop_type"] == "chile"
