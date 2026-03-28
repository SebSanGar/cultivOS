"""Tests for batch health portfolio grid on intel dashboard."""

from datetime import datetime

import pytest


def _seed_farm_with_fields(db, farm_name, fields_data):
    """Seed a farm with fields and optional NDVI data for health scoring.

    fields_data: list of dicts with keys: name, ndvi_mean (optional)
    """
    from cultivos.db.models import Farm, Field, NDVIResult

    farm = Farm(name=farm_name, state="Jalisco")
    db.add(farm)
    db.flush()

    field_ids = []
    for fd in fields_data:
        field = Field(name=fd["name"], farm_id=farm.id, crop_type="maiz", hectares=5.0)
        db.add(field)
        db.flush()
        field_ids.append(field.id)

        if fd.get("ndvi_mean") is not None:
            db.add(NDVIResult(
                field_id=field.id,
                ndvi_mean=fd["ndvi_mean"],
                ndvi_std=0.05,
                ndvi_min=fd["ndvi_mean"] - 0.1,
                ndvi_max=fd["ndvi_mean"] + 0.1,
                pixels_total=1000,
                stress_pct=max(0, (0.4 - fd["ndvi_mean"]) * 100) if fd["ndvi_mean"] < 0.4 else 5.0,
                zones=[],
            ))

    db.commit()
    return farm.id, field_ids


# ── API Tests ──────────────────────────────────────────────────────────


def test_batch_health_with_data(client, db, admin_headers):
    """POST /api/intel/batch-health returns scores for seeded fields."""
    _, field_ids = _seed_farm_with_fields(db, "Granja Norte", [
        {"name": "Parcela A", "ndvi_mean": 0.75},
        {"name": "Parcela B", "ndvi_mean": 0.30},
    ])
    resp = client.post(
        "/api/intel/batch-health",
        json={"field_ids": field_ids},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2
    a = next(r for r in data["results"] if r["field_name"] == "Parcela A")
    b = next(r for r in data["results"] if r["field_name"] == "Parcela B")
    assert a["score"] is not None
    assert b["score"] is not None


def test_batch_health_empty_ids(client, admin_headers):
    """POST with empty field_ids returns empty results."""
    resp = client.post(
        "/api/intel/batch-health",
        json={"field_ids": []},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_batch_health_invalid_ids(client, admin_headers):
    """POST with non-existent field IDs returns null entries."""
    resp = client.post(
        "/api/intel/batch-health",
        json={"field_ids": [99999]},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["score"] is None
    assert results[0]["field_name"] is None


# ── Frontend Tests ─────────────────────────────────────────────────────


def test_intel_html_has_batch_health_section(client):
    """intel.html contains the batch health grid section."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="intel-batch-health"' in html
    assert "Salud por Campo" in html


def test_intel_js_has_batch_health_loader(client):
    """intel.js contains loadBatchHealth function."""
    resp = client.get("/intel.js")
    assert resp.status_code == 200
    js = resp.text
    assert "loadBatchHealth" in js
    assert "batch-health" in js


def test_intel_js_renders_color_classes(client):
    """intel.js uses health color classes for batch grid cards."""
    resp = client.get("/intel.js")
    js = resp.text
    assert "healthClass" in js
    assert "batch-health-card" in js


def test_intel_js_handles_empty_batch(client):
    """intel.js shows empty state when no fields exist."""
    resp = client.get("/intel.js")
    js = resp.text
    assert "Sin datos de salud" in js


def test_batch_health_grid_css_exists(client):
    """styles.css contains batch health grid styles."""
    resp = client.get("/styles.css")
    css = resp.text
    assert "batch-health-grid" in css
    assert "batch-health-card" in css
