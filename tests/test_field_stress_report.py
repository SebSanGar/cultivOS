"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/stress-report — multi-sensor stress index."""

import pytest
from datetime import datetime


def _make_farm(client, db):
    from cultivos.db.models import Farm, Field
    farm = Farm(name="Rancho Stress Test", state="Jalisco")
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Campo Uno", crop_type="maiz", hectares=5.0)
    db.add(field)
    db.commit()
    return farm, field


def _seed_health(db, field_id, score):
    from cultivos.db.models import HealthScore
    hs = HealthScore(field_id=field_id, score=score, sources=["health"], breakdown={})
    db.add(hs)
    db.commit()
    return hs


def _seed_ndvi(db, field_id, ndvi_mean, stress_pct=10.0):
    from cultivos.db.models import NDVIResult
    ndvi = NDVIResult(
        field_id=field_id,
        ndvi_mean=ndvi_mean,
        ndvi_std=0.05,
        ndvi_min=ndvi_mean - 0.1,
        ndvi_max=ndvi_mean + 0.1,
        pixels_total=1000,
        stress_pct=stress_pct,
        zones=[],
    )
    db.add(ndvi)
    db.commit()
    return ndvi


def _seed_thermal(db, field_id, stress_pct=20.0, irrigation_deficit=False):
    from cultivos.db.models import ThermalResult
    tr = ThermalResult(
        field_id=field_id,
        temp_mean=32.0,
        temp_std=2.0,
        temp_min=28.0,
        temp_max=38.0,
        pixels_total=1000,
        stress_pct=stress_pct,
        irrigation_deficit=irrigation_deficit,
    )
    db.add(tr)
    db.commit()
    return tr


def _seed_soil(db, field_id, ph=7.0):
    from cultivos.db.models import SoilAnalysis
    soil = SoilAnalysis(
        field_id=field_id,
        ph=ph,
        organic_matter_pct=2.5,
        nitrogen_ppm=30.0,
        sampled_at=datetime.utcnow(),
    )
    db.add(soil)
    db.commit()
    return soil


def test_response_keys_present(client, db):
    farm, field = _make_farm(client, db)
    _seed_health(db, field.id, score=60.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-report")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "field_id" in data
    assert "field_name" in data
    assert "stress_level" in data
    assert "stress_score" in data
    assert "contributing_factors" in data
    assert "recommended_priority" in data


def test_all_sources_critical(client, db):
    """health=30 + thermal + NDVI<0.4 + pH out-of-range → critical."""
    farm, field = _make_farm(client, db)
    _seed_health(db, field.id, score=30.0)
    _seed_thermal(db, field.id, stress_pct=50.0, irrigation_deficit=True)
    _seed_ndvi(db, field.id, ndvi_mean=0.3)
    _seed_soil(db, field.id, ph=8.5)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-report")
    assert resp.status_code == 200
    data = resp.json()
    assert data["stress_level"] == "critical"
    assert data["stress_score"] >= 75
    assert data["recommended_priority"] == 5


def test_health_only_partial(client, db):
    """Only health score seeded → still returns result with stress_level."""
    farm, field = _make_farm(client, db)
    _seed_health(db, field.id, score=70.0)  # stress base = 30 → medium

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-report")
    assert resp.status_code == 200
    data = resp.json()
    assert data["stress_level"] in ("low", "medium")
    assert 0 <= data["stress_score"] <= 100
    # contributing_factors should have health entry
    sources = [f["source"] for f in data["contributing_factors"]]
    assert "health" in sources


def test_thermal_adds_factor(client, db):
    """Thermal irrigation_deficit adds 15 points and appears in contributing_factors."""
    farm, field = _make_farm(client, db)
    _seed_health(db, field.id, score=70.0)   # base stress = 30
    _seed_thermal(db, field.id, stress_pct=40.0, irrigation_deficit=True)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-report")
    assert resp.status_code == 200
    data = resp.json()
    # 30 + 15 = 45 → medium/high boundary
    assert data["stress_score"] >= 44
    sources = [f["source"] for f in data["contributing_factors"]]
    assert "thermal" in sources


def test_ndvi_below_threshold(client, db):
    """NDVI mean < 0.4 adds 10 points and appears in contributing_factors."""
    farm, field = _make_farm(client, db)
    _seed_health(db, field.id, score=70.0)   # base stress = 30
    _seed_ndvi(db, field.id, ndvi_mean=0.35)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/stress-report")
    assert resp.status_code == 200
    data = resp.json()
    # 30 + 10 = 40 → medium
    assert data["stress_score"] >= 39
    sources = [f["source"] for f in data["contributing_factors"]]
    assert "ndvi" in sources


def test_404_unknown_field(client):
    resp = client.get("/api/farms/9999/fields/9999/stress-report")
    assert resp.status_code == 404
