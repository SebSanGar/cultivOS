"""Tests for GET /api/cooperatives/{coop_id}/outbreak-risk endpoint.

Task #184: Cooperative disease outbreak risk aggregate.
Composes compute_disease_risk_assessment per field across all member farms.
"""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    Cooperative,
    Farm,
    Field,
    NDVIResult,
    SoilAnalysis,
    WeatherRecord,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_coop(db, name="Cooperativa Test"):
    coop = Cooperative(name=name, state="Jalisco")
    db.add(coop)
    db.commit()
    return coop


def _make_farm(db, coop_id, name="Rancho Test"):
    farm = Farm(name=name, state="Jalisco", cooperative_id=coop_id, total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_weather(db, farm_id, humidity_pct=80.0, temp_c=28.0, days_ago=0):
    """Add a WeatherRecord to trigger humidity/temp risk factors."""
    rec = WeatherRecord(
        farm_id=farm_id,
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        wind_kmh=10.0,
        description="test",
        recorded_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(rec)
    db.commit()
    return rec


def _add_ndvi_drop(db, field_id):
    """Add two NDVI results showing >20% drop → triggers disease risk."""
    now = datetime.utcnow()
    older = NDVIResult(
        field_id=field_id,
        ndvi_mean=0.80,
        ndvi_std=0.10,
        ndvi_min=0.60,
        ndvi_max=0.90,
        pixels_total=1000,
        stress_pct=5.0,
        zones="{}",
        created_at=now - timedelta(days=30),
    )
    newer = NDVIResult(
        field_id=field_id,
        ndvi_mean=0.50,  # 37.5% drop from 0.80
        ndvi_std=0.15,
        ndvi_min=0.30,
        ndvi_max=0.70,
        pixels_total=1000,
        stress_pct=30.0,
        zones="{}",
        created_at=now,
    )
    db.add_all([older, newer])
    db.commit()


def _add_low_ph_soil(db, field_id):
    """Add soil with pH < 5.5 → triggers Fusarium risk."""
    now = datetime.utcnow()
    soil = SoilAnalysis(
        field_id=field_id,
        ph=4.8,
        organic_matter_pct=2.0,
        nitrogen_ppm=20.0,
        phosphorus_ppm=10.0,
        potassium_ppm=100.0,
        sampled_at=now,
        created_at=now,
    )
    db.add(soil)
    db.commit()


# ── Tests ──────────────────────────────────────────────────────────────────────


def test_unknown_coop_returns_404(client):
    resp = client.get("/api/cooperatives/99999/outbreak-risk")
    assert resp.status_code == 404


def test_empty_coop_no_farms(client, db):
    coop = _make_coop(db)
    resp = client.get(f"/api/cooperatives/{coop.id}/outbreak-risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["total_high_risk_fields"] == 0
    assert data["total_medium_risk_fields"] == 0
    assert data["overall_risk_level"] == "low"
    assert data["farms"] == []


def test_no_sensor_data_overall_risk_low(client, db):
    """Farms with fields but no sensor data → all risk scores = 0 → low."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    _make_field(db, farm.id, name="Campo 1")
    _make_field(db, farm.id, name="Campo 2")

    resp = client.get(f"/api/cooperatives/{coop.id}/outbreak-risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_risk_level"] == "low"
    assert data["total_high_risk_fields"] == 0
    assert data["total_medium_risk_fields"] == 0
    assert data["total_low_risk_fields"] == 2
    assert data["affected_farms_count"] == 0
    assert data["top_risk_crop"] is None


def test_response_key_schema(client, db):
    """Verify all expected keys are present in response."""
    coop = _make_coop(db)
    resp = client.get(f"/api/cooperatives/{coop.id}/outbreak-risk")
    assert resp.status_code == 200
    data = resp.json()
    for key in [
        "cooperative_id", "total_high_risk_fields", "total_medium_risk_fields",
        "total_low_risk_fields", "top_risk_crop", "affected_farms_count",
        "overall_risk_level", "farms",
    ]:
        assert key in data, f"Missing key: {key}"


def test_two_farms_with_disease_data(client, db):
    """Two farms with high-risk triggers → correct counts + affected farms."""
    coop = _make_coop(db)

    # Farm 1: 2 fields, high humidity → both get +20
    farm1 = _make_farm(db, coop.id, name="Rancho A")
    f1a = _make_field(db, farm1.id, name="Campo 1A", crop_type="maiz")
    f1b = _make_field(db, farm1.id, name="Campo 1B", crop_type="frijol")
    _add_weather(db, farm1.id, humidity_pct=85.0, temp_c=37.0)
    # humidity(+20) + temp(+10) = 30 → medium
    # Also add NDVI drop on f1a → +25 = 55 → high
    _add_ndvi_drop(db, f1a.id)

    # Farm 2: 1 field, low pH soil + humidity
    farm2 = _make_farm(db, coop.id, name="Rancho B")
    f2a = _make_field(db, farm2.id, name="Campo 2A", crop_type="maiz")
    _add_weather(db, farm2.id, humidity_pct=75.0)
    _add_low_ph_soil(db, f2a.id)
    # humidity(+20) + pH(+15) = 35 → medium

    resp = client.get(f"/api/cooperatives/{coop.id}/outbreak-risk")
    assert resp.status_code == 200
    data = resp.json()

    # f1a: 55 → high, f1b: 30 → medium, f2a: 35 → medium
    assert data["total_high_risk_fields"] == 1
    assert data["total_medium_risk_fields"] == 2
    assert data["affected_farms_count"] == 2  # both farms have >= medium risk
    assert data["overall_risk_level"] == "high"  # at least one high field
    assert data["top_risk_crop"] == "maiz"  # maiz appears on both high/medium fields


def test_top_risk_crop_most_affected(client, db):
    """top_risk_crop is the crop type with the most high+medium risk fields."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    _add_weather(db, farm.id, humidity_pct=90.0, temp_c=36.0)

    # 2 frijol fields (both medium), 1 maiz field (medium)
    _make_field(db, farm.id, name="F1", crop_type="frijol")
    _make_field(db, farm.id, name="F2", crop_type="frijol")
    _make_field(db, farm.id, name="F3", crop_type="maiz")

    resp = client.get(f"/api/cooperatives/{coop.id}/outbreak-risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["top_risk_crop"] == "frijol"


def test_farm_detail_structure(client, db):
    """Each farm entry has correct sub-structure."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id, name="Rancho Detail")
    _make_field(db, farm.id, name="C1")
    _make_field(db, farm.id, name="C2")

    resp = client.get(f"/api/cooperatives/{coop.id}/outbreak-risk")
    assert resp.status_code == 200
    farm_entry = resp.json()["farms"][0]
    assert farm_entry["farm_id"] == farm.id
    assert farm_entry["farm_name"] == "Rancho Detail"
    assert farm_entry["total_fields"] == 2
    for key in ["high_risk_fields", "medium_risk_fields", "low_risk_fields"]:
        assert key in farm_entry


def test_affected_farms_only_counts_medium_or_high(client, db):
    """affected_farms_count excludes farms where all fields are low risk."""
    coop = _make_coop(db)

    # Farm with high humidity + high temp → medium risk (20+10=30)
    farm_risky = _make_farm(db, coop.id, name="Risky")
    _make_field(db, farm_risky.id, name="CR")
    _add_weather(db, farm_risky.id, humidity_pct=85.0, temp_c=36.0)

    # Farm with no sensor data → all low risk
    farm_safe = _make_farm(db, coop.id, name="Safe")
    _make_field(db, farm_safe.id, name="CS")

    resp = client.get(f"/api/cooperatives/{coop.id}/outbreak-risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["affected_farms_count"] == 1
    assert len(data["farms"]) == 2


def test_overall_risk_medium_when_no_high(client, db):
    """overall_risk is medium when there are medium-risk fields but no high."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    _make_field(db, farm.id)
    _add_weather(db, farm.id, humidity_pct=80.0)
    # humidity +20 only → score=20 → low (<=25)
    # Need humidity+temp for medium: +20+10 = 30 → medium
    _add_weather(db, farm.id, humidity_pct=80.0, temp_c=36.0)

    resp = client.get(f"/api/cooperatives/{coop.id}/outbreak-risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_risk_level"] == "medium"
    assert data["total_medium_risk_fields"] >= 1
    assert data["total_high_risk_fields"] == 0
