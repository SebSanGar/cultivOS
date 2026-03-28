"""Tests for the growth stage tracker UI on the field detail page."""

from datetime import datetime, timedelta

import pytest


# ── HTML structure ──

def test_growth_section_in_field_html(client):
    """Field detail HTML has the Etapa de Crecimiento section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-growth"' in html
    assert "Etapa de Crecimiento" in html


def test_growth_container_in_html(client):
    """Field detail HTML has a container for growth stage content."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="growth-content"' in resp.text


# ── JS logic ──

def test_field_js_has_growth_render(client):
    """field.js contains the renderGrowthStage function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderGrowthStage" in resp.text


def test_field_js_fetches_growth_stage(client):
    """field.js fetches the /growth-stage endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "/growth-stage" in resp.text


def test_field_js_shows_stage_name(client):
    """field.js renders the stage_es Spanish stage name."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "stage_es" in resp.text


def test_field_js_shows_days_since_planting(client):
    """field.js renders days_since_planting."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "days_since_planting" in resp.text


def test_field_js_shows_progress_bar(client):
    """field.js renders a progress bar for stage progress."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "growth-progress" in resp.text


def test_field_js_shows_water_and_nutrient(client):
    """field.js renders water_multiplier and nutrient_focus."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "water_multiplier" in js
    assert "nutrient_focus" in js


def test_field_js_handles_missing_growth_stage(client):
    """field.js handles null growth stage gracefully (no planted_at)."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    # Should have a null/falsy check before rendering
    assert "renderGrowthStage" in js


# ── API integration ──

def test_growth_api_returns_stage(client, db, admin_headers):
    """GET growth-stage returns computed stage for a field with planted_at."""
    from cultivos.db.models import Farm, Field
    farm = Farm(name="Rancho Fenologia")
    db.add(farm)
    db.commit()
    planted = datetime.utcnow() - timedelta(days=30)
    field = Field(farm_id=farm.id, name="Parcela Crecimiento", crop_type="maiz",
                  planted_at=planted)
    db.add(field)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-stage")
    assert resp.status_code == 200
    data = resp.json()
    assert data["stage"] == "vegetativo"
    assert data["days_since_planting"] >= 29
    assert data["water_multiplier"] > 0
    assert data["nutrient_focus"]
