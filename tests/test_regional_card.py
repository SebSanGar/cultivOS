"""Tests for the regional recommendations card on the field detail page.

Verifies that the field detail page contains the regional context card
showing Jalisco-specific climate, soil, season, and treatment recommendations.
"""

import pytest
from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis
from datetime import datetime


@pytest.fixture
def jalisco_farm_with_field(db):
    """Create a Jalisco farm with a field that has health data."""
    farm = Farm(name="Rancho Regional", state="Jalisco", municipality="Zapopan")
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id,
        name="Parcela Maiz",
        crop_type="maiz",
        hectares=10.0,
    )
    db.add(field)
    db.flush()
    db.add(HealthScore(
        field_id=field.id,
        score=55.0,
        trend="stable",
        scored_at=datetime(2026, 3, 15),
    ))
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


# -- API integration: recommendations endpoint returns region context --

def test_recommendations_returns_region_profile(client, jalisco_farm_with_field):
    """GET /api/farms/{id}/recommendations includes region metadata."""
    fid = jalisco_farm_with_field["farm_id"]
    resp = client.get(f"/api/farms/{fid}/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "region" in data
    region = data["region"]
    assert region["climate_zone"] == "tropical_subtropical"
    assert region["currency"] == "MXN"
    assert "maiz" in region["key_crops"]


def test_recommendations_returns_field_recommendations(client, jalisco_farm_with_field):
    """Recommendations list is populated for field with health score."""
    fid = jalisco_farm_with_field["farm_id"]
    resp = client.get(f"/api/farms/{fid}/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["recommendations"]) > 0
    rec = data["recommendations"][0]
    assert "tratamiento" in rec
    assert "urgencia" in rec


# -- HTML structure: field detail page has regional section --

def test_field_html_has_regional_section(client):
    """field.html contains the regional recommendations section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-regional"' in html


def test_field_html_has_regional_content_container(client):
    """field.html has the regional-content container div."""
    resp = client.get("/campo")
    html = resp.text
    assert 'id="regional-content"' in html


# -- Frontend JS: field.js has regional rendering --

def test_field_js_has_render_regional(client):
    """field.js contains the renderRegionalCard function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderRegionalCard" in js


def test_field_js_fetches_recommendations(client):
    """field.js fetches the /recommendations endpoint."""
    resp = client.get("/field.js")
    js = resp.text
    assert "/recommendations" in js


def test_field_js_renders_climate_zone(client):
    """field.js renders the climate zone label."""
    resp = client.get("/field.js")
    js = resp.text
    assert "climate_zone" in js or "clima" in js.lower()


# -- CSS: styles for regional card --

def test_regional_card_styles_present(client):
    """styles.css has regional card styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "regional" in css.lower()
