"""Tests for the economic impact card on the farm dashboard."""

import pytest
from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from datetime import datetime


@pytest.fixture
def farm_with_data(db):
    """Create a farm with fields, health scores, and treatments."""
    farm = Farm(name="Rancho Economico", state="Jalisco", total_hectares=50)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Maiz", crop_type="maiz", hectares=25)
    db.add(field)
    db.flush()

    db.add(HealthScore(
        field_id=field.id,
        score=72.0,
        trend="improving",
        scored_at=datetime(2026, 3, 1),
    ))
    db.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=65.0,
        problema="Baja fertilidad",
        causa_probable="suelo pobre",
        tratamiento="Composta",
        urgencia="media",
        prevencion="rotacion",
        organic=True,
        costo_estimado_mxn=500,
    ))
    db.commit()
    return {"farm_id": farm.id}


@pytest.fixture
def empty_farm(db):
    """Create a farm with no fields."""
    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=0)
    db.add(farm)
    db.commit()
    return {"farm_id": farm.id}


# -- API integration --

def test_economic_impact_returns_savings(client, farm_with_data):
    """GET /economic-impact returns MXN savings breakdown."""
    fid = farm_with_data["farm_id"]
    resp = client.get(f"/api/farms/{fid}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_savings_mxn" in data
    assert "water_savings_mxn" in data
    assert "fertilizer_savings_mxn" in data
    assert "yield_improvement_mxn" in data
    assert data["total_savings_mxn"] >= 0


def test_economic_impact_no_fields(client, empty_farm):
    """GET /economic-impact handles farm with no fields gracefully."""
    fid = empty_farm["farm_id"]
    resp = client.get(f"/api/farms/{fid}/economic-impact")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_savings_mxn"] == 0
    assert "nota" in data


# -- HTML structure --

def test_economic_impact_container_in_dashboard(client):
    """Dashboard HTML has the economic-impact container div."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="economic-impact-panel"' in html


def test_economic_impact_hidden_by_default(client):
    """Economic impact container is hidden by default."""
    resp = client.get("/")
    html = resp.text
    assert 'id="economic-impact-panel"' in html
    # Find the full opening tag and verify display:none
    idx = html.index('id="economic-impact-panel"')
    tag_start = html.rfind('<div', 0, idx)
    tag_end = html.index('>', idx)
    tag_snippet = html[tag_start:tag_end + 1]
    assert 'display:none' in tag_snippet


# -- Frontend JS --

def test_app_js_has_economic_impact_loader(client):
    """app.js contains the loadEconomicImpact function."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "loadEconomicImpact" in js


def test_app_js_fetches_economic_impact(client):
    """app.js fetches the /economic-impact endpoint."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "/economic-impact" in js


def test_app_js_renders_mxn_currency(client):
    """app.js formats savings in MXN currency."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "MXN" in js or "mxn" in js.lower()


# -- CSS --

def test_economic_impact_styles_present(client):
    """styles.css has economic impact card styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "economic" in css.lower() or "econ-" in css
