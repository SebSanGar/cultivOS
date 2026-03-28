"""Tests for enhanced farm comparison — sortable columns, health trend, CSV export."""

from datetime import datetime

import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


def _seed_farm(db, name, fields_data):
    """Create a farm with fields, health scores, and treatments."""
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


# ── API: health_trend field ──────────────────────────────────────────


def test_compare_returns_health_trend_improving(client, db, admin_headers):
    """Farm with increasing health scores returns 'improving' trend."""
    farm = _seed_farm(db, "Rancho Mejora", [
        {"name": "P1", "hectares": 10, "health_scores": [50, 65, 80]},
    ])
    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert entry["trend"] == "improving"


def test_compare_returns_health_trend_declining(client, db, admin_headers):
    """Farm with decreasing health scores returns 'declining' trend."""
    farm = _seed_farm(db, "Rancho Baja", [
        {"name": "P1", "hectares": 10, "health_scores": [80, 65, 50]},
    ])
    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert entry["trend"] == "declining"


def test_compare_returns_health_trend_stable(client, db, admin_headers):
    """Farm with flat health scores returns 'stable' trend."""
    farm = _seed_farm(db, "Rancho Estable", [
        {"name": "P1", "hectares": 10, "health_scores": [70, 71, 70]},
    ])
    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert entry["trend"] == "stable"


def test_compare_returns_health_trend_null_no_scores(client, db, admin_headers):
    """Farm with no health scores returns null trend."""
    farm = _seed_farm(db, "Rancho Vacio", [
        {"name": "P1", "hectares": 10, "health_scores": []},
    ])
    resp = client.get(
        f"/api/intel/compare?farm_ids={farm.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    entry = resp.json()["farms"][0]
    assert entry["trend"] is None


# ── Frontend: sortable headers ───────────────────────────────────────


def test_intel_compare_has_sortable_headers(client):
    """Comparison table JS renders sortable headers with data-sort attributes."""
    resp = client.get("/intel.js")
    assert resp.status_code == 200
    js = resp.text
    assert 'data-sort="farm_name"' in js
    assert 'data-sort="avg_health"' in js
    assert 'data-sort="total_hectares"' in js


def test_intel_compare_has_sort_indicator_class(client):
    """Header cells in JS template have compare-sortable class for cursor styling."""
    resp = client.get("/intel.js")
    assert resp.status_code == 200
    assert "compare-sortable" in resp.text


# ── Frontend: CSV export button ──────────────────────────────────────


def test_intel_compare_has_csv_export_button(client):
    """Comparison panel has a CSV export button."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert 'id="compare-csv-btn"' in resp.text


def test_intel_compare_csv_button_has_spanish_label(client):
    """CSV export button has Spanish label."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert "Exportar CSV" in resp.text


# ── Frontend: trend display ──────────────────────────────────────────


def test_intel_js_has_trend_rendering(client):
    """intel.js contains trend rendering logic for comparison table."""
    resp = client.get("/intel.js")
    assert resp.status_code == 200
    assert "compare-trend" in resp.text


def test_intel_js_has_sort_function(client):
    """intel.js contains the sort comparison function."""
    resp = client.get("/intel.js")
    assert resp.status_code == 200
    assert "sortCompareTable" in resp.text


def test_intel_js_has_csv_export_function(client):
    """intel.js contains the CSV export function."""
    resp = client.get("/intel.js")
    assert resp.status_code == 200
    assert "exportCompareCSV" in resp.text


# ── CSS: sortable styling ────────────────────────────────────────────


def test_styles_has_sortable_cursor(client):
    """styles.css has cursor:pointer for sortable headers."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    assert "compare-sortable" in resp.text
