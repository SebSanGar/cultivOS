"""Tests for GET /api/cooperatives/{coop_id}/fodecijal-readiness endpoint.

Task #186: Cooperative FODECIJAL readiness score — aggregate 5 sub-scores
across all member farms for grant readiness assessment.
"""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    AncestralMethod,
    Cooperative,
    Farm,
    Field,
    HealthScore,
    NDVIResult,
    SoilAnalysis,
    ThermalResult,
    TreatmentRecord,
    WeatherRecord,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_coop(db, name="Cooperativa FODECIJAL"):
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


def _add_health(db, field_id, score, days_ago=0):
    scored_at = datetime.utcnow() - timedelta(days=days_ago)
    hs = HealthScore(field_id=field_id, score=score, scored_at=scored_at)
    db.add(hs)
    db.commit()
    return hs


def _add_ndvi(db, field_id, days_ago=0):
    analyzed_at = datetime.utcnow() - timedelta(days=days_ago)
    ndvi = NDVIResult(
        field_id=field_id,
        ndvi_mean=0.65,
        ndvi_min=0.3,
        ndvi_max=0.9,
        ndvi_std=0.1,
        pixels_total=1000,
        stress_pct=5.0,
        zones={"healthy": 0.9, "stressed": 0.1},
        analyzed_at=analyzed_at,
    )
    db.add(ndvi)
    db.commit()
    return ndvi


def _add_soil(db, field_id, days_ago=0):
    sampled_at = datetime.utcnow() - timedelta(days=days_ago)
    soil = SoilAnalysis(
        field_id=field_id,
        ph=6.5,
        organic_matter_pct=3.5,
        nitrogen_ppm=40,
        phosphorus_ppm=25,
        potassium_ppm=180,
        sampled_at=sampled_at,
    )
    db.add(soil)
    db.commit()
    return soil


def _add_weather(db, farm_id, days_ago=0):
    recorded_at = datetime.utcnow() - timedelta(days=days_ago)
    wr = WeatherRecord(
        farm_id=farm_id,
        temp_c=28.0,
        humidity_pct=65.0,
        wind_kmh=10.0,
        description="parcialmente nublado",
        recorded_at=recorded_at,
    )
    db.add(wr)
    db.commit()
    return wr


def _add_treatment(db, field_id, organic=True, days_ago=0):
    created_at = datetime.utcnow() - timedelta(days=days_ago)
    tr = TreatmentRecord(
        field_id=field_id,
        health_score_used=60.0,
        problema="plaga",
        causa_probable="insectos",
        tratamiento="compost orgánico",
        costo_estimado_mxn=500,
        urgencia="baja",
        prevencion="rotación de cultivos",
        organic=organic,
        created_at=created_at,
    )
    db.add(tr)
    db.commit()
    return tr


def _add_ancestral(db, name, crops, months):
    am = AncestralMethod(
        name=name,
        description_es="Práctica ancestral de prueba",
        region="Jalisco",
        practice_type="soil_management",
        crops=crops,
        benefits_es="Mejora la salud del suelo",
        applicable_months=months,
        ecological_benefit=4,
    )
    db.add(am)
    db.commit()
    return am


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_unknown_coop_returns_404(client):
    resp = client.get("/api/cooperatives/99999/fodecijal-readiness")
    assert resp.status_code == 404


def test_empty_coop_graceful_zeros(client, db):
    """Cooperative with no farms → all sub-scores 0, overall 0."""
    coop = _make_coop(db)
    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["overall_score"] == 0.0
    assert data["farm_count"] == 0
    assert data["field_count"] == 0
    assert len(data["sub_scores"]) == 5
    for sub in data["sub_scores"]:
        assert sub["score"] == 0.0


def test_weights_sum_to_one(client, db):
    """All 5 sub-score weights must sum to 1.0."""
    coop = _make_coop(db)
    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    data = resp.json()
    total_weight = sum(s["weight"] for s in data["sub_scores"])
    assert abs(total_weight - 1.0) < 0.001


def test_response_key_schema(client, db):
    """Verify exact keys in response."""
    coop = _make_coop(db)
    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    data = resp.json()
    assert "cooperative_id" in data
    assert "overall_score" in data
    assert "sub_scores" in data
    assert "farm_count" in data
    assert "field_count" in data
    sub = data["sub_scores"][0]
    assert "name" in sub
    assert "score" in sub
    assert "weight" in sub
    assert "evidence_es" in sub


def test_coop_with_all_data_high_score(client, db):
    """Cooperative with comprehensive data across all sub-scores → high overall."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id, crop_type="maiz")

    now = datetime.utcnow()
    current_month = now.month

    # Data completeness: all 5 types present
    _add_health(db, field.id, 80.0)
    _add_ndvi(db, field.id)
    _add_soil(db, field.id)
    _add_weather(db, farm.id)
    _add_treatment(db, field.id, organic=True)

    # Health score for regen trajectory
    _add_health(db, field.id, 75.0, days_ago=15)

    # TEK: add ancestral method matching field crop + current month
    _add_ancestral(db, "Milpa", ["maiz"], [current_month])

    # Treatment with followup health for effectiveness
    _add_treatment(db, field.id, organic=True, days_ago=20)
    _add_health(db, field.id, 85.0, days_ago=10)  # post-treatment improvement

    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_score"] > 30.0  # should be well above zero with all data
    assert data["farm_count"] == 1
    assert data["field_count"] == 1


def test_no_data_farm_zero_sub_scores(client, db):
    """Farm with no fields/data → sub-scores are 0 or near-0."""
    coop = _make_coop(db)
    _make_farm(db, coop.id)  # empty farm

    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_score"] == 0.0
    assert data["farm_count"] == 1


def test_sensor_freshness_sub_score_recent_data(client, db):
    """Fresh sensor data (within 14 days) → high sensor freshness score."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)

    # All sensors within last 3 days
    _add_health(db, field.id, 70.0, days_ago=1)
    _add_ndvi(db, field.id, days_ago=2)
    _add_soil(db, field.id, days_ago=3)
    _add_weather(db, farm.id, days_ago=1)

    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    data = resp.json()

    sensor_sub = [s for s in data["sub_scores"] if s["name"] == "sensor_freshness"][0]
    assert sensor_sub["score"] > 50.0  # all fresh sensors → high score


def test_multiple_farms_averaged(client, db):
    """Two farms: one with data, one empty → scores averaged."""
    coop = _make_coop(db)

    # Farm 1: has some data
    farm1 = _make_farm(db, coop.id, name="Rancho Rico")
    field1 = _make_field(db, farm1.id)
    _add_health(db, field1.id, 80.0)
    _add_ndvi(db, field1.id)
    _add_soil(db, field1.id)
    _add_weather(db, farm1.id)
    _add_treatment(db, field1.id, organic=True)

    # Farm 2: empty
    _make_farm(db, coop.id, name="Rancho Vacio")

    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    data = resp.json()
    assert data["farm_count"] == 2
    # Overall should be lower than with just farm1 since farm2 drags average down
    assert data["overall_score"] < 100.0


def test_evidence_bullets_in_spanish(client, db):
    """All evidence strings should be non-empty Spanish text."""
    coop = _make_coop(db)
    _make_farm(db, coop.id)
    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    data = resp.json()
    for sub in data["sub_scores"]:
        assert len(sub["evidence_es"]) > 0
        assert isinstance(sub["evidence_es"], str)


def test_overall_score_is_weighted_avg(client, db):
    """Overall score = sum(sub.score * sub.weight) for all sub-scores."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 70.0)
    _add_ndvi(db, field.id)

    resp = client.get(f"/api/cooperatives/{coop.id}/fodecijal-readiness")
    data = resp.json()

    expected = sum(s["score"] * s["weight"] for s in data["sub_scores"])
    assert abs(data["overall_score"] - round(expected, 2)) < 0.1
