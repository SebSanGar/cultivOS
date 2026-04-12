"""Tests for #185 — WhatsApp-ready farm status message.

GET /api/farms/{farm_id}/whatsapp-status
Returns a 3-line Spanish plain-text message suitable for WhatsApp delivery.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, SoilAnalysis, WeatherRecord


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _farm(db, name="Rancho WhatsApp"):
    f = Farm(name=name, municipality="Guadalajara", state="Jalisco", total_hectares=10.0)
    db.add(f)
    db.commit()
    return f


def _field(db, farm_id, crop_type="maiz"):
    f = Field(farm_id=farm_id, name="Lote A", crop_type=crop_type, hectares=5.0)
    db.add(f)
    db.commit()
    return f


def _weather_normal(db, farm_id):
    db.add(WeatherRecord(
        farm_id=farm_id, temp_c=22.0, humidity_pct=60.0,
        wind_kmh=10.0, rainfall_mm=5.0, description="soleado",
        forecast_3day=[], recorded_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()


def _soil_critical(db, field_id):
    db.add(SoilAnalysis(
        field_id=field_id, moisture_pct=5.0, ph=6.5,
        organic_matter_pct=2.0, nitrogen_ppm=20.0,
        sampled_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()


def _weather_extreme_heat(db, farm_id):
    db.add(WeatherRecord(
        farm_id=farm_id, temp_c=42.0, humidity_pct=15.0,
        wind_kmh=10.0, rainfall_mm=0.0, description="calor extremo",
        forecast_3day=[], recorded_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()


# ── Tests ────────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/whatsapp-status")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response always has farm_id, message_es, has_alerts, generated_at."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/whatsapp-status")
    assert r.status_code == 200
    data = r.json()
    assert "farm_id" in data
    assert "message_es" in data
    assert "has_alerts" in data
    assert "generated_at" in data


def test_farm_id_matches(client, db):
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/whatsapp-status")
    assert r.status_code == 200
    assert r.json()["farm_id"] == farm.id


def test_safe_farm_has_no_alerts(client, db):
    """Farm with no stress → has_alerts=False, message_es contains farm name."""
    farm = _farm(db, name="Rancho Tranquilo")
    _field(db, farm.id)
    _weather_normal(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/whatsapp-status")
    assert r.status_code == 200
    data = r.json()
    assert data["has_alerts"] is False
    assert "Rancho Tranquilo" in data["message_es"]


def test_critical_farm_has_alerts(client, db):
    """Farm with critical stress → has_alerts=True."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _soil_critical(db, field.id)
    _weather_extreme_heat(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/whatsapp-status")
    assert r.status_code == 200
    data = r.json()
    assert data["has_alerts"] is True


def test_message_es_is_3_lines(client, db):
    """message_es has exactly 3 newline-separated lines."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/whatsapp-status")
    data = r.json()
    lines = data["message_es"].strip().split("\n")
    assert len(lines) == 3


def test_message_line1_contains_farm_name(client, db):
    """First line of message includes the farm name."""
    farm = _farm(db, name="Granja Jalisco")
    r = client.get(f"/api/farms/{farm.id}/whatsapp-status")
    lines = r.json()["message_es"].strip().split("\n")
    assert "Granja Jalisco" in lines[0]


def test_message_line2_contains_alerta_when_critical(client, db):
    """Second line contains 'Alerta:' prefix when alerts are active."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _soil_critical(db, field.id)
    _weather_extreme_heat(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/whatsapp-status")
    data = r.json()
    if data["has_alerts"]:
        lines = data["message_es"].strip().split("\n")
        assert "Alerta:" in lines[1] or "alerta" in lines[1].lower()


def test_generated_at_is_valid_iso(client, db):
    """generated_at is a valid ISO datetime string."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/whatsapp-status")
    assert r.status_code == 200
    generated_at = r.json()["generated_at"]
    # Should not raise
    datetime.fromisoformat(generated_at)
