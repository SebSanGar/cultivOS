"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/stress-index endpoint."""

import pytest
from datetime import datetime

from cultivos.db.models import (
    Alert, Farm, Field, HealthScore, SoilAnalysis,
    ThermalResult, WeatherRecord,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_farm(db):
    farm = Farm(name="Test Farm", municipality="Guadalajara", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, crop_type="maiz"):
    field = Field(farm_id=farm_id, name="Lote A", crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_thermal(db, field_id, stress_pct):
    tr = ThermalResult(
        field_id=field_id,
        temp_mean=30.0, temp_std=2.0, temp_min=25.0, temp_max=38.0,
        pixels_total=1000,
        stress_pct=stress_pct,
        analyzed_at=datetime.utcnow(),
    )
    db.add(tr)
    db.commit()
    return tr


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/fields/99999/stress-index")
    assert r.status_code == 404


def test_404_unknown_field(client, db):
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/99999/stress-index")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response contains all required schema fields."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-index")
    assert r.status_code == 200
    data = r.json()
    assert "field_id" in data
    assert "stress_index" in data
    assert "stress_level" in data
    assert "components" in data
    assert "recommendation_es" in data
    components = data["components"]
    assert "water" in components
    assert "disease" in components
    assert "thermal" in components


def test_no_signals_returns_valid_response(client, db):
    """With no sensor data, services return zero stress — endpoint succeeds."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-index")
    assert r.status_code == 200
    data = r.json()
    # water=0 (urgency=none), disease=0, thermal=50 (no record → neutral)
    # composite = 0*0.4 + 0*0.35 + 50*0.25 = 12.5
    assert data["stress_index"] == pytest.approx(12.5, abs=2.0)
    assert data["stress_level"] in ("none", "low")


def test_all_zero_signals_returns_none_level(client, db):
    """When all components are zero, stress_level is none and index near 0."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_thermal(db, field.id, stress_pct=0.0)
    # No alerts (water urgency = none = 0), no disease data (risk_score = 0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-index")
    assert r.status_code == 200
    data = r.json()
    # water=0, disease=0, thermal=0 → index=0
    assert data["stress_index"] == pytest.approx(0.0, abs=5.0)
    assert data["stress_level"] in ("none", "low")


def test_high_thermal_stress_raises_index(client, db):
    """High thermal stress_pct raises the composite index."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_thermal(db, field.id, stress_pct=100.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-index")
    assert r.status_code == 200
    data = r.json()
    # thermal=100, water=0 (no data → urgency none), disease=0
    # composite = 0*0.4 + 0*0.35 + 100*0.25 = 25.0
    assert data["components"]["thermal"] == pytest.approx(100.0, abs=1.0)
    assert data["stress_index"] > 0.0
    assert data["stress_index"] > 10.0  # thermal contribution clearly visible


def test_stress_level_thresholds(client, db):
    """Stress level categories are correctly assigned."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_thermal(db, field.id, stress_pct=0.0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-index")
    assert r.status_code == 200
    data = r.json()
    level = data["stress_level"]
    idx = data["stress_index"]
    # Verify level matches index
    if idx < 20:
        assert level == "none"
    elif idx < 40:
        assert level == "low"
    elif idx < 60:
        assert level == "moderate"
    elif idx < 80:
        assert level == "high"
    else:
        assert level == "critical"


def test_composite_formula_weights(client, db):
    """composite = water*0.4 + disease*0.35 + thermal*0.25."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_thermal(db, field.id, stress_pct=80.0)
    # stress_pct=80 >= 40 threshold → water_stress picks up thermal factor → urgency=low → water=25
    # No disease data → disease=0
    # thermal=80
    # expected = 25*0.4 + 0*0.35 + 80*0.25 = 10 + 0 + 20 = 30.0

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-index")
    assert r.status_code == 200
    data = r.json()
    assert data["stress_index"] == pytest.approx(30.0, abs=2.0)
    assert data["components"]["thermal"] == pytest.approx(80.0, abs=1.0)
