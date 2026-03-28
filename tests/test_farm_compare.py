"""Tests for farm comparison dashboard API — GET /api/intel/compare."""

from datetime import datetime

import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


def _seed_farm(db, name, fields_data):
    """Create a farm with fields and optional health scores / treatments.

    fields_data: list of dicts with keys:
        name, crop_type, hectares, health_scores (list of floats), treatments (int count)
    """
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

        for j in range(fd.get("treatments", 0)):
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


# ── Happy path: returns data for all requested farms ──────────────────


def test_compare_returns_all_requested_farms(client, db, admin_headers):
    """Comparison returns a result entry for every requested farm."""
    f1 = _seed_farm(db, "Rancho A", [
        {"name": "Parcela 1", "crop_type": "maiz", "hectares": 10, "health_scores": [70, 75], "treatments": 2},
    ])
    f2 = _seed_farm(db, "Rancho B", [
        {"name": "Parcela 2", "crop_type": "aguacate", "hectares": 20, "health_scores": [85], "treatments": 1},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={f1.id},{f2.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["farms"]) == 2

    ids_returned = {f["farm_id"] for f in data["farms"]}
    assert ids_returned == {f1.id, f2.id}


def test_compare_includes_health_and_yield(client, db, admin_headers):
    """Each farm entry includes health score summary and yield prediction."""
    farm = _seed_farm(db, "Rancho Test", [
        {"name": "Parcela 1", "crop_type": "maiz", "hectares": 10, "health_scores": [72]},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]

    assert "avg_health" in entry
    assert entry["avg_health"] is not None
    assert "total_hectares" in entry
    assert "yield_total_kg" in entry
    assert entry["yield_total_kg"] > 0
    assert "treatment_count" in entry
    assert "field_count" in entry


def test_compare_health_values_correct(client, db, admin_headers):
    """Verify health is averaged from latest scores per field."""
    farm = _seed_farm(db, "Rancho", [
        {"name": "P1", "health_scores": [60, 80]},  # latest = 80
        {"name": "P2", "health_scores": [90]},       # latest = 90
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    entry = resp.json()["farms"][0]
    # avg of latest scores: (80 + 90) / 2 = 85
    assert entry["avg_health"] == 85.0


# ── Missing farm returns 404 ─────────────────────────────────────────


def test_compare_missing_farm_returns_404(client, db, admin_headers):
    """If any requested farm_id does not exist, return 404."""
    farm = _seed_farm(db, "Rancho Real", [
        {"name": "P1", "health_scores": [70]},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id},99999",
        headers=admin_headers,
    )
    assert resp.status_code == 404
    body = resp.json()
    assert "99999" in body.get("detail", str(body))


# ── Empty fields handled gracefully ──────────────────────────────────


def test_compare_farm_with_no_fields(client, db, admin_headers):
    """Farm with zero fields returns entry with null/zero health and yield."""
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


def test_compare_field_with_no_health_scores(client, db, admin_headers):
    """Field with no health scores still returns graceful entry."""
    farm = _seed_farm(db, "Rancho Nuevo", [
        {"name": "P1", "crop_type": "maiz", "hectares": 5, "health_scores": []},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert entry["field_count"] == 1
    assert entry["avg_health"] is None
    assert entry["yield_total_kg"] == 0


# ── Edge cases ────────────────────────────────────────────────────────


def test_compare_no_farm_ids_returns_422(client, db, admin_headers):
    """Missing farm_ids query param returns validation error."""
    resp = client.get("/api/intel/compare", headers=admin_headers)
    assert resp.status_code == 422


def test_compare_has_auth_dependency(client, db, admin_headers):
    """Endpoint has admin/researcher auth dependency (returns 200 with admin token)."""
    farm = _seed_farm(db, "Rancho", [{"name": "P1", "health_scores": [70]}])
    resp = client.get(f"/api/intel/compare?farm_ids={farm.id}", headers=admin_headers)
    assert resp.status_code == 200
