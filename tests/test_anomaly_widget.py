"""Tests for anomaly detection widget — field-level anomaly endpoint."""

from datetime import datetime

import pytest

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult


def _make_farm(db):
    farm = Farm(name="Granja Test", municipality="Zapopan", state="Jalisco")
    db.add(farm)
    db.flush()
    return farm


def _make_field(db, farm, name="Lote A", crop="maiz"):
    field = Field(farm_id=farm.id, name=name, crop_type=crop, hectares=10)
    db.add(field)
    db.flush()
    return field


def _make_ndvi(db, field_id, mean, analyzed_at):
    db.add(NDVIResult(
        field_id=field_id, ndvi_mean=mean, ndvi_std=0.05,
        ndvi_min=mean - 0.1, ndvi_max=mean + 0.1,
        pixels_total=1000, stress_pct=5.0, zones={},
        analyzed_at=analyzed_at,
    ))


# ── API endpoint tests ──


def test_field_anomalies_health_drop(client, db):
    """GET returns health drop anomalies when score drops >15 points."""
    farm = _make_farm(db)
    field = _make_field(db, farm)

    db.add(HealthScore(field_id=field.id, score=80, scored_at=datetime(2026, 3, 1)))
    db.add(HealthScore(field_id=field.id, score=60, scored_at=datetime(2026, 3, 15)))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
    assert resp.status_code == 200
    data = resp.json()
    assert "health_anomalies" in data
    assert "ndvi_anomalies" in data
    assert len(data["health_anomalies"]) == 1
    assert data["health_anomalies"][0]["type"] == "health_drop"
    assert data["health_anomalies"][0]["drop"] == 20


def test_field_anomalies_ndvi_drop(client, db):
    """GET returns NDVI drop anomalies when latest drops >20% below average."""
    farm = _make_farm(db)
    field = _make_field(db, farm, name="Lote B", crop="agave")

    _make_ndvi(db, field.id, 0.70, datetime(2026, 1, 1))
    _make_ndvi(db, field.id, 0.72, datetime(2026, 2, 1))
    _make_ndvi(db, field.id, 0.50, datetime(2026, 3, 1))  # ~29% drop
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["ndvi_anomalies"]) == 1
    assert data["ndvi_anomalies"][0]["type"] == "ndvi_drop"


def test_field_anomalies_no_anomalies(client, db):
    """GET returns empty lists when field has no anomalies."""
    farm = _make_farm(db)
    field = _make_field(db, farm, name="Lote C")

    db.add(HealthScore(field_id=field.id, score=75, scored_at=datetime(2026, 3, 1)))
    db.add(HealthScore(field_id=field.id, score=73, scored_at=datetime(2026, 3, 15)))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["health_anomalies"]) == 0
    assert len(data["ndvi_anomalies"]) == 0


def test_field_anomalies_no_data(client, db):
    """GET returns empty lists when field has no health/NDVI data."""
    farm = _make_farm(db)
    field = _make_field(db, farm, name="Lote D")
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health_anomalies"] == []
    assert data["ndvi_anomalies"] == []


def test_field_anomalies_404_bad_field(client, db):
    """GET returns 404 if field doesn't exist."""
    farm = _make_farm(db)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/9999/anomalies")
    assert resp.status_code == 404


def test_field_anomalies_includes_recommendations(client, db):
    """Anomaly results include Spanish-language recommendations."""
    farm = _make_farm(db)
    field = _make_field(db, farm, name="Lote E")

    db.add(HealthScore(field_id=field.id, score=80, scored_at=datetime(2026, 3, 1)))
    db.add(HealthScore(field_id=field.id, score=55, scored_at=datetime(2026, 3, 15)))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/anomalies")
    data = resp.json()
    rec = data["health_anomalies"][0]["recommendation"]
    assert "Alerta" in rec
    assert "Lote E" in rec
