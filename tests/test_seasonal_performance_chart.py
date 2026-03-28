"""Tests for the per-field seasonal performance chart on the field detail page."""

import pytest
from datetime import datetime as dt

from cultivos.db.models import Farm, Field, HealthScore


@pytest.fixture
def seasonal_farm(db):
    """Create a farm with a field and multi-year health scores spanning seasons."""
    farm = Farm(
        name="Rancho Temporal",
        owner_name="Test Owner",
        location_lat=20.67,
        location_lon=-103.35,
        total_hectares=50,
        municipality="Zapopan",
        state="Jalisco",
        country="MX",
    )
    db.add(farm)
    db.flush()

    field = Field(
        name="Parcela Norte",
        farm_id=farm.id,
        hectares=10,
        crop_type="maiz",
    )
    db.add(field)
    db.flush()

    # Create health scores across 2 years and 2 seasons
    # Temporal 2025 (Jun-Oct 2025)
    for i, day in enumerate([dt(2025, 7, 1), dt(2025, 8, 15), dt(2025, 9, 10)]):
        db.add(HealthScore(
            field_id=field.id,
            score=70 + i * 5,
            scored_at=day,
            sources=["ndvi"],
        ))

    # Secas 2025 (Nov 2025 - May 2026)
    for i, day in enumerate([dt(2025, 12, 1), dt(2026, 2, 15)]):
        db.add(HealthScore(
            field_id=field.id,
            score=55 + i * 5,
            scored_at=day,
            sources=["ndvi"],
        ))

    # Temporal 2024 (Jun-Oct 2024)
    for i, day in enumerate([dt(2024, 7, 15), dt(2024, 9, 20)]):
        db.add(HealthScore(
            field_id=field.id,
            score=60 + i * 5,
            scored_at=day,
            sources=["ndvi"],
        ))

    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


# ── HTML structure tests ──

def test_seasonal_performance_section_in_html(client):
    """Field detail HTML has the seasonal performance chart section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    text = resp.text
    assert 'id="section-seasonal-perf"' in text
    assert 'Rendimiento Estacional' in text


def test_seasonal_performance_has_canvas(client):
    """Section contains a canvas element for Chart.js."""
    resp = client.get("/campo")
    text = resp.text
    assert 'id="seasonal-perf-chart"' in text


def test_seasonal_performance_placeholder(client):
    """Section shows placeholder text."""
    resp = client.get("/campo")
    text = resp.text
    assert 'id="seasonal-perf-content"' in text


# ── API response tests (via seasonal endpoint) ──

def test_seasonal_endpoint_returns_multi_year(client, seasonal_farm, admin_headers):
    """GET /api/farms/{id}/fields/{id}/seasonal returns data for multiple seasons."""
    fid = seasonal_farm["farm_id"]
    flid = seasonal_farm["field_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{flid}/seasonal")
    assert resp.status_code == 200
    data = resp.json()
    assert "seasons" in data
    seasons = data["seasons"]
    assert len(seasons) >= 2  # at least 2 season entries


def test_seasonal_endpoint_single_year_filter(client, seasonal_farm, admin_headers):
    """GET seasonal with ?year=2025 returns only 2025 seasons."""
    fid = seasonal_farm["farm_id"]
    flid = seasonal_farm["field_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{flid}/seasonal?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    seasons = data["seasons"]
    for s in seasons:
        assert s["year"] == 2025


def test_seasonal_endpoint_empty_field(client, admin_headers):
    """Seasonal endpoint on field with no health scores returns empty seasons."""
    farm = client.post("/api/farms", json={
        "name": "Vacio", "owner_name": "Test", "location_lat": 20.0,
        "location_lon": -103.0, "total_hectares": 5,
        "municipality": "Test", "state": "Jalisco", "country": "MX",
    }, headers=admin_headers).json()
    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Empty", "hectares": 1,
    }, headers=admin_headers).json()
    resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/seasonal")
    assert resp.status_code == 200
    data = resp.json()
    assert data["seasons"] == []


# ── JS function tests ──

def test_field_js_has_seasonal_performance_render(client):
    """field.js contains the renderSeasonalPerformance function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    text = resp.text
    assert "renderSeasonalPerformance" in text


def test_field_js_fetches_seasonal_data(client):
    """field.js fetches the seasonal endpoint in the Promise.all block."""
    resp = client.get("/field.js")
    text = resp.text
    assert "/seasonal" in text
    assert "renderSeasonalPerformance" in text
