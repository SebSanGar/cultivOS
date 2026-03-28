"""Tests for farm comparison UI on intel page."""

from datetime import datetime

import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


def _seed_farm(db, name, fields_data):
    """Create a farm with fields and optional health scores / treatments."""
    farm = Farm(name=name, owner_name="Test", total_hectares=100)
    db.add(farm)
    db.flush()

    for fd in fields_data:
        field = Field(
            farm_id=farm.id,
            name=fd["name"],
            crop_type=fd.get("crop_type", "maiz"),
            hectares=fd.get("hectares", 10.0),
        )
        db.add(field)
        db.flush()

        for i, score_val in enumerate(fd.get("health_scores", [])):
            hs = HealthScore(
                field_id=field.id,
                score=score_val,
                trend="stable",
                sources=["ndvi"],
                breakdown={"ndvi": score_val},
                scored_at=datetime(2026, 3, 1 + i),
            )
            db.add(hs)

        for _ in range(fd.get("treatments", 0)):
            tr = TreatmentRecord(
                field_id=field.id,
                health_score_used=50.0,
                problema="Deficiencia",
                causa_probable="Bajo nitrogeno",
                tratamiento="Composta",
                costo_estimado_mxn=500,
                urgencia="media",
                prevencion="Rotacion",
                organic=True,
            )
            db.add(tr)

    db.commit()
    return farm


# ── HTML structure tests ─────────────────────────────────────────────


def test_intel_has_farm_compare_section(client):
    """Intel page has the farm comparison container element."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert 'id="intel-farm-compare"' in resp.text


def test_intel_has_farm_compare_title(client):
    """Farm comparison section has the correct Spanish title."""
    resp = client.get("/intel")
    assert "Comparacion de Granjas" in resp.text


def test_intel_has_farm_select_control(client):
    """Intel page has the multi-select farm picker element."""
    resp = client.get("/intel")
    assert 'id="farm-compare-select"' in resp.text


# ── API integration tests ────────────────────────────────────────────


def test_compare_renders_with_two_farms(client, db, admin_headers):
    """Comparison endpoint returns data for 2 farms with correct fields."""
    f1 = _seed_farm(db, "Rancho Norte", [
        {"name": "P1", "hectares": 15, "health_scores": [72, 78], "treatments": 3},
    ])
    f2 = _seed_farm(db, "Rancho Sur", [
        {"name": "P2", "hectares": 25, "health_scores": [85], "treatments": 1},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={f1.id},{f2.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["farms"]) == 2

    names = {f["farm_name"] for f in data["farms"]}
    assert "Rancho Norte" in names
    assert "Rancho Sur" in names

    for farm in data["farms"]:
        assert "avg_health" in farm
        assert "yield_total_kg" in farm
        assert "treatment_count" in farm
        assert "total_hectares" in farm
        assert "field_count" in farm


def test_compare_handles_single_farm(client, db, admin_headers):
    """Single farm comparison returns valid data."""
    farm = _seed_farm(db, "Rancho Solo", [
        {"name": "P1", "hectares": 10, "health_scores": [65], "treatments": 2},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["farms"]) == 1
    assert data["farms"][0]["farm_name"] == "Rancho Solo"
    assert data["farms"][0]["avg_health"] == 65.0
    assert data["farms"][0]["treatment_count"] == 2


def test_compare_handles_empty_farm(client, db, admin_headers):
    """Farm with no fields returns null health and zero yield/treatments."""
    farm = _seed_farm(db, "Rancho Vacio", [])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert entry["field_count"] == 0
    assert entry["avg_health"] is None
    assert entry["yield_total_kg"] == 0
    assert entry["treatment_count"] == 0


def test_farms_list_available_for_picker(client, db, admin_headers):
    """GET /api/farms returns farms that can populate the comparison picker."""
    _seed_farm(db, "Rancho Test", [{"name": "P1", "health_scores": [70]}])
    resp = client.get("/api/farms", headers=admin_headers)
    assert resp.status_code == 200
