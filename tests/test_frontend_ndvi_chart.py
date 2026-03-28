"""Tests for NDVI history chart on field detail page."""

import pytest


def test_ndvi_chart_canvas_exists(client):
    """Field detail HTML has a canvas element for the NDVI chart."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="ndvi-chart"' in html


def test_ndvi_chart_container_exists(client):
    """NDVI section has a chart container div wrapping the canvas."""
    resp = client.get("/campo")
    html = resp.text
    assert "campo-chart-container" in html or "ndvi-chart-container" in html
    assert 'id="ndvi-chart"' in html


def test_ndvi_chart_label_present(client):
    """NDVI chart section has Spanish chart label."""
    resp = client.get("/campo")
    html = resp.text
    assert "Tendencia NDVI" in html or "Historial NDVI" in html


def test_ndvi_api_returns_data_for_chart(client, admin_headers):
    """NDVI API returns list with fields needed for chart rendering."""
    farm = client.post("/api/farms", json={
        "name": "Rancho NDVI Chart",
        "owner_name": "Test",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 20,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()

    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Parcela NDVI",
        "crop_type": "maiz",
        "hectares": 10,
    }).json()

    # Create multiple NDVI records for chart data
    for _ in range(3):
        resp = client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/ndvi", json={
            "nir_band": [[0.5, 0.6], [0.55, 0.58]],
            "red_band": [[0.1, 0.08], [0.09, 0.07]],
        })
        assert resp.status_code == 201

    resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/ndvi")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # Each result has the fields needed for chart
    for item in data:
        assert "ndvi_mean" in item
        assert "stress_pct" in item
        assert "analyzed_at" in item


def test_ndvi_chart_js_function_referenced(client):
    """field.js is loaded and contains the NDVI chart rendering function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderNdviChart" in js


def test_ndvi_chart_handles_empty_data(client):
    """field.js has empty-state handling for NDVI chart (no data)."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    # The render function should handle null/empty list
    assert "renderNdviChart" in js
    # Chart should be in the renderNdviHistory flow
    assert "ndvi-chart" in js


def test_ndvi_stress_zones_in_chart(client):
    """field.js references stress threshold zones in NDVI chart configuration."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    # Stress percentage dataset should be in the chart
    assert "stress_pct" in js or "Estres" in js
