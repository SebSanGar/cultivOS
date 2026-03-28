"""Tests for enhanced farm comparison — sortable table, sparklines, CSV export."""

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


# ── API: health_history field ────────────────────────────────────────


def test_compare_returns_health_history(client, db, admin_headers):
    """Compare endpoint includes health_history list of recent scores per farm."""
    farm = _seed_farm(db, "Rancho Historia", [
        {"name": "P1", "hectares": 10, "health_scores": [60, 65, 72, 78]},
        {"name": "P2", "hectares": 15, "health_scores": [50, 55]},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert "health_history" in entry
    assert isinstance(entry["health_history"], list)
    assert len(entry["health_history"]) > 0
    # History values should be floats
    for val in entry["health_history"]:
        assert isinstance(val, (int, float))


def test_compare_health_history_empty_when_no_scores(client, db, admin_headers):
    """Farm with no health scores has empty health_history."""
    farm = _seed_farm(db, "Rancho Sin Datos", [
        {"name": "P1", "hectares": 10, "health_scores": []},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert entry["health_history"] == []


def test_compare_health_history_limited_to_recent(client, db, admin_headers):
    """Health history returns at most 10 recent average scores."""
    # Create farm with many scores
    farm = _seed_farm(db, "Rancho Mucho", [
        {"name": "P1", "hectares": 10, "health_scores": list(range(40, 60))},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert len(entry["health_history"]) <= 10


# ── HTML: sortable headers ───────────────────────────────────────────


def test_intel_has_sortable_header_attributes(client):
    """Intel comparison section has sortable column headers."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert "data-sort" in resp.text
    assert "sortCompareTable" in resp.text


def test_intel_has_compare_csv_button(client):
    """Intel comparison section has a CSV export button."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert "exportCompareCSV" in resp.text


def test_intel_has_sparkline_container(client):
    """Intel comparison section has sparkline containers for health trend."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert "compare-sparkline" in resp.text


# ── Compare endpoint returns trend field ─────────────────────────────


def test_compare_returns_trend(client, db, admin_headers):
    """Compare endpoint includes health trend label per farm."""
    farm = _seed_farm(db, "Rancho Trend", [
        {"name": "P1", "hectares": 10, "health_scores": [60, 65, 72]},
    ])

    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert "trend" in entry
    assert entry["trend"] in ("improving", "stable", "declining", None)
