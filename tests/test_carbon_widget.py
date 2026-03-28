"""Tests for the soil carbon widget on the field detail page."""

import pytest
from cultivos.db.models import Farm, Field, SoilAnalysis
from datetime import datetime


@pytest.fixture
def farm_with_carbon(db):
    """Farm with field that has soil analyses with organic matter data."""
    farm = Farm(name="Rancho Carbon", state="Jalisco", total_hectares=40)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Carbono", crop_type="maiz", hectares=20)
    db.add(field)
    db.flush()

    # Three soil records to establish a trend (compute_carbon_trend requires 3+)
    db.add(SoilAnalysis(
        field_id=field.id, ph=6.5, organic_matter_pct=2.5,
        nitrogen_ppm=30, phosphorus_ppm=15, potassium_ppm=150,
        depth_cm=30, sampled_at=datetime(2026, 1, 15),
    ))
    db.add(SoilAnalysis(
        field_id=field.id, ph=6.5, organic_matter_pct=2.8,
        nitrogen_ppm=32, phosphorus_ppm=16, potassium_ppm=155,
        depth_cm=30, sampled_at=datetime(2026, 2, 15),
    ))
    db.add(SoilAnalysis(
        field_id=field.id, ph=6.6, organic_matter_pct=3.0,
        nitrogen_ppm=35, phosphorus_ppm=18, potassium_ppm=160,
        depth_cm=30, sampled_at=datetime(2026, 3, 15),
    ))
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


@pytest.fixture
def farm_no_soil(db):
    """Farm with field that has no soil analyses."""
    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=10)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Sin Datos", crop_type="frijol", hectares=5)
    db.add(field)
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


# -- API integration --

def test_carbon_returns_report_with_data(client, farm_with_carbon):
    """GET /carbon returns SOC estimate and trend when soil data exists."""
    fid = farm_with_carbon["farm_id"]
    field_id = farm_with_carbon["field_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/carbon")
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_id"] == field_id
    assert data["soc_actual"] is not None
    assert data["soc_actual"]["soc_tonnes_per_ha"] > 0
    assert data["soc_actual"]["clasificacion"] in ("bajo", "adecuado", "alto")
    assert data["tendencia"] in ("ganando", "estable", "perdiendo", "datos_insuficientes")
    assert data["registros"] >= 2
    assert isinstance(data["resumen"], str)
    assert len(data["resumen"]) > 0


def test_carbon_handles_missing_soil(client, farm_no_soil):
    """GET /carbon returns graceful empty response when no soil data."""
    fid = farm_no_soil["farm_id"]
    field_id = farm_no_soil["field_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/carbon")
    assert resp.status_code == 200
    data = resp.json()
    assert data["soc_actual"] is None
    assert data["tendencia"] == "datos_insuficientes"
    assert data["registros"] == 0


def test_carbon_shows_correct_trend(client, farm_with_carbon):
    """With increasing organic matter, trend should be 'ganando'."""
    fid = farm_with_carbon["farm_id"]
    field_id = farm_with_carbon["field_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/carbon")
    data = resp.json()
    # OM went from 2.5 to 3.0 → SOC increasing → ganando
    assert data["tendencia"] == "ganando"
    assert data["cambio_soc_tonnes_per_ha"] > 0


def test_carbon_404_bad_farm(client):
    """GET /carbon returns 404 for nonexistent farm."""
    resp = client.get("/api/farms/9999/fields/1/carbon")
    assert resp.status_code == 404


def test_carbon_404_bad_field(client, farm_with_carbon):
    """GET /carbon returns 404 for nonexistent field."""
    fid = farm_with_carbon["farm_id"]
    resp = client.get(f"/api/farms/{fid}/fields/9999/carbon")
    assert resp.status_code == 404


# -- HTML structure --

def test_carbon_section_in_field_html(client):
    """Field detail HTML has the carbon widget section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="carbon-content"' in html


def test_carbon_section_has_title(client):
    """Field detail HTML has the section title."""
    resp = client.get("/campo")
    html = resp.text
    assert "Carbono del Suelo" in html


# -- Frontend JS --

def test_field_js_has_render_carbon(client):
    """field.js contains the renderCarbon function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderCarbon" in js


def test_field_js_fetches_carbon(client):
    """field.js fetches the /carbon endpoint."""
    resp = client.get("/field.js")
    js = resp.text
    assert "/carbon" in js


def test_field_js_shows_soc_value(client):
    """field.js renders the SOC tonnes per hectare value."""
    resp = client.get("/field.js")
    js = resp.text
    assert "soc_tonnes_per_ha" in js


def test_field_js_shows_trend(client):
    """field.js renders the trend indicator."""
    resp = client.get("/field.js")
    js = resp.text
    assert "tendencia" in js
