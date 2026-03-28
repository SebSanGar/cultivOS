"""Tests for sensor fusion validation card on intel dashboard."""

from datetime import datetime, timedelta

import pytest


# ── Helper: seed a field with sensor data ──────────────────────────────

def _seed_field_with_sensors(db, farm_id, field_name, ndvi_vals=None, thermal_vals=None, soil_vals=None):
    """Seed a field and optionally attach NDVI, thermal, soil records."""
    from cultivos.db.models import Farm, Field, NDVIResult, ThermalResult, SoilAnalysis

    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        farm = Farm(id=farm_id, name="Test Farm", state="Jalisco")
        db.add(farm)
        db.flush()

    field = Field(name=field_name, farm_id=farm.id, crop_type="maiz", hectares=5.0)
    db.add(field)
    db.flush()

    now = datetime.utcnow()

    if ndvi_vals:
        db.add(NDVIResult(
            field_id=field.id,
            ndvi_mean=ndvi_vals["ndvi_mean"],
            ndvi_std=ndvi_vals.get("ndvi_std", 0.05),
            ndvi_min=ndvi_vals.get("ndvi_min", 0.2),
            ndvi_max=ndvi_vals.get("ndvi_max", 0.9),
            pixels_total=ndvi_vals.get("pixels_total", 10000),
            stress_pct=ndvi_vals.get("stress_pct", 10.0),
            zones=ndvi_vals.get("zones", []),
            analyzed_at=now,
        ))

    if thermal_vals:
        db.add(ThermalResult(
            field_id=field.id,
            temp_mean=thermal_vals.get("temp_mean", 28.0),
            temp_std=thermal_vals.get("temp_std", 3.0),
            temp_max=thermal_vals.get("temp_max", 35.0),
            temp_min=thermal_vals.get("temp_min", 20.0),
            pixels_total=thermal_vals.get("pixels_total", 10000),
            stress_pct=thermal_vals.get("stress_pct", 10.0),
            irrigation_deficit=thermal_vals.get("irrigation_deficit", False),
            analyzed_at=now,
        ))

    if soil_vals:
        db.add(SoilAnalysis(
            field_id=field.id,
            ph=soil_vals.get("ph", 6.5),
            organic_matter_pct=soil_vals.get("organic_matter_pct", 4.0),
            nitrogen_ppm=soil_vals.get("nitrogen_ppm", 30.0),
            phosphorus_ppm=soil_vals.get("phosphorus_ppm", 20.0),
            potassium_ppm=soil_vals.get("potassium_ppm", 150.0),
            moisture_pct=soil_vals.get("moisture_pct", 35.0),
            sampled_at=now,
        ))

    db.commit()
    return field


# ── API Tests ──────────────────────────────────────────────────────────


def test_sensor_fusion_endpoint_empty_db(client, admin_headers):
    """Endpoint returns valid response with no fields."""
    resp = client.get("/api/intel/sensor-fusion", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_fields"] == 0
    assert data["fields_with_data"] == 0
    assert data["avg_confidence"] == 0
    assert data["total_contradictions"] == 0
    assert data["fields"] == []


def test_sensor_fusion_endpoint_with_consistent_sensors(client, db, admin_headers):
    """Field with consistent NDVI+thermal+soil gets high confidence, no contradictions."""
    _seed_field_with_sensors(
        db, farm_id=1, field_name="Parcela Norte",
        ndvi_vals={"ndvi_mean": 0.7, "stress_pct": 5.0},
        thermal_vals={"stress_pct": 8.0, "temp_mean": 28.0},
        soil_vals={"ph": 6.5, "organic_matter_pct": 4.0},
    )
    resp = client.get("/api/intel/sensor-fusion", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_fields"] == 1
    assert data["fields_with_data"] == 1
    assert data["avg_confidence"] > 0.5
    assert data["total_contradictions"] == 0
    assert len(data["fields"]) == 1
    f = data["fields"][0]
    assert f["field_name"] == "Parcela Norte"
    assert f["confidence"] > 0.5
    assert f["contradictions"] == []
    assert "ndvi" in f["sensors_used"]
    assert "thermal" in f["sensors_used"]
    assert "soil" in f["sensors_used"]


def test_sensor_fusion_endpoint_with_contradiction(client, db, admin_headers):
    """Field with NDVI healthy but thermal stressed shows contradiction."""
    _seed_field_with_sensors(
        db, farm_id=1, field_name="Parcela Sur",
        ndvi_vals={"ndvi_mean": 0.75, "stress_pct": 5.0},
        thermal_vals={"stress_pct": 50.0, "temp_mean": 40.0},
    )
    resp = client.get("/api/intel/sensor-fusion", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_contradictions"] >= 1
    f = data["fields"][0]
    assert len(f["contradictions"]) >= 1
    assert f["contradictions"][0]["tag"] == "ndvi_thermal_mismatch"


def test_sensor_fusion_endpoint_multiple_fields(client, db, admin_headers):
    """Multiple fields — one consistent, one with contradiction — aggregates correctly."""
    _seed_field_with_sensors(
        db, farm_id=1, field_name="Campo A",
        ndvi_vals={"ndvi_mean": 0.7, "stress_pct": 5.0},
        thermal_vals={"stress_pct": 8.0, "temp_mean": 28.0},
    )
    _seed_field_with_sensors(
        db, farm_id=1, field_name="Campo B",
        ndvi_vals={"ndvi_mean": 0.75, "stress_pct": 5.0},
        thermal_vals={"stress_pct": 50.0, "temp_mean": 40.0},
    )
    resp = client.get("/api/intel/sensor-fusion", headers=admin_headers)
    data = resp.json()
    assert data["total_fields"] == 2
    assert data["fields_with_data"] == 2
    assert data["total_contradictions"] >= 1
    # Campo B should have contradiction
    campo_b = next(f for f in data["fields"] if f["field_name"] == "Campo B")
    assert len(campo_b["contradictions"]) >= 1


def test_sensor_fusion_endpoint_no_sensor_data(client, db, admin_headers):
    """Field exists but has no sensor data — excluded from fields_with_data."""
    from cultivos.db.models import Farm, Field
    farm = Farm(name="Empty Farm", state="Jalisco")
    db.add(farm)
    db.flush()
    field = Field(name="Empty Field", farm_id=farm.id)
    db.add(field)
    db.commit()

    resp = client.get("/api/intel/sensor-fusion", headers=admin_headers)
    data = resp.json()
    assert data["total_fields"] == 1
    assert data["fields_with_data"] == 0
    assert data["fields"] == []


def test_sensor_fusion_requires_admin_or_researcher(app, db):
    """Farmer role gets 403 on sensor fusion endpoint."""
    import os
    from fastapi.testclient import TestClient
    from cultivos.db.session import get_db

    # Enable auth for this test so role enforcement is active
    old_val = os.environ.get("AUTH_ENABLED")
    os.environ["AUTH_ENABLED"] = "true"
    from cultivos.config import get_settings
    get_settings.cache_clear()
    try:
        from cultivos.app import create_app
        auth_app = create_app()
        auth_app.dependency_overrides[get_db] = lambda: db
        with TestClient(auth_app, raise_server_exceptions=False) as c:
            c.post("/api/auth/register", json={
                "username": "testfarmer", "password": "secret123", "role": "farmer"
            })
            resp = c.post("/api/auth/login", json={
                "username": "testfarmer", "password": "secret123"
            })
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            resp = c.get("/api/intel/sensor-fusion", headers=headers)
            assert resp.status_code == 403
    finally:
        if old_val is None:
            os.environ.pop("AUTH_ENABLED", None)
        else:
            os.environ["AUTH_ENABLED"] = old_val
        get_settings.cache_clear()


# ── Frontend Tests ─────────────────────────────────────────────────────


def test_intel_html_has_fusion_panel(client):
    """intel.html contains the sensor fusion panel div."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="intel-sensor-fusion"' in html
    assert "Validacion de Sensores" in html


def test_intel_js_has_fusion_loader(client):
    """intel.js contains the loadSensorFusion function."""
    resp = client.get("/intel.js")
    assert resp.status_code == 200
    js = resp.text
    assert "loadSensorFusion" in js
    assert "sensor-fusion" in js
