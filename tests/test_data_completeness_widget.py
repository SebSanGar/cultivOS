"""Tests for the data completeness widget on the field detail page."""

import pytest
from cultivos.db.models import (
    Farm, Field, SoilAnalysis, NDVIResult, ThermalResult,
    TreatmentRecord, WeatherRecord,
)
from datetime import datetime


@pytest.fixture
def farm_complete(db):
    """Farm with one field that has all 5 data types present."""
    farm = Farm(name="Rancho Completo", state="Jalisco", total_hectares=50)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Maiz", crop_type="maiz", hectares=25)
    db.add(field)
    db.flush()

    db.add(SoilAnalysis(field_id=field.id, ph=6.5, organic_matter_pct=3.2, nitrogen_ppm=40, phosphorus_ppm=20, potassium_ppm=180, sampled_at=datetime(2026, 3, 1)))
    db.add(NDVIResult(field_id=field.id, ndvi_mean=0.72, ndvi_std=0.1, ndvi_min=0.4, ndvi_max=0.9, pixels_total=1000, stress_pct=5.0, zones=[{"zone": "A", "mean": 0.72}], analyzed_at=datetime(2026, 3, 1)))
    db.add(ThermalResult(field_id=field.id, temp_mean=28.0, temp_std=3.0, temp_min=22.0, temp_max=35.0, pixels_total=1000, stress_pct=10.0, analyzed_at=datetime(2026, 3, 1)))
    db.add(TreatmentRecord(field_id=field.id, health_score_used=65.0, problema="test", causa_probable="test", tratamiento="Composta", urgencia="media", prevencion="rotacion", organic=True, costo_estimado_mxn=500))
    db.add(WeatherRecord(farm_id=farm.id, temp_c=25.0, humidity_pct=60.0, wind_kmh=10.0, rainfall_mm=0.0, description="despejado", forecast_3day=[], recorded_at=datetime(2026, 3, 1)))
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


@pytest.fixture
def farm_empty(db):
    """Farm with one field that has no data."""
    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=10)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Vacia", crop_type="frijol", hectares=5)
    db.add(field)
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


# -- API integration --

def test_completeness_returns_field_scores(client, farm_complete):
    """GET /data-completeness returns per-field completeness with all flags."""
    fid = farm_complete["farm_id"]
    resp = client.get(f"/api/farms/{fid}/data-completeness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_score"] == 100.0
    field_data = data["fields"][0]
    assert field_data["has_soil"] is True
    assert field_data["has_ndvi"] is True
    assert field_data["has_thermal"] is True
    assert field_data["has_treatments"] is True
    assert field_data["has_weather"] is True
    assert field_data["score"] == 100.0


def test_completeness_empty_field(client, farm_empty):
    """GET /data-completeness returns zeros for empty field."""
    fid = farm_empty["farm_id"]
    resp = client.get(f"/api/farms/{fid}/data-completeness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_score"] == 0.0
    field_data = data["fields"][0]
    assert field_data["score"] == 0.0
    assert field_data["has_soil"] is False


# -- HTML structure --

def test_completeness_section_in_field_html(client):
    """Field detail HTML has the data-completeness section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="completeness-content"' in html


def test_completeness_section_has_title(client):
    """Field detail HTML has the section title."""
    resp = client.get("/campo")
    html = resp.text
    assert "Completitud de Datos" in html


# -- Frontend JS --

def test_field_js_has_render_function(client):
    """field.js contains the renderDataCompleteness function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderDataCompleteness" in js


def test_field_js_fetches_completeness(client):
    """field.js fetches the /data-completeness endpoint."""
    resp = client.get("/field.js")
    js = resp.text
    assert "data-completeness" in js


def test_field_js_shows_sensor_types(client):
    """field.js renders individual sensor type indicators."""
    resp = client.get("/field.js")
    js = resp.text
    # Should reference the 5 sensor types
    assert "has_soil" in js
    assert "has_ndvi" in js
    assert "has_thermal" in js


# -- CSS --

def test_completeness_styles_present(client):
    """styles.css has completeness widget styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "completeness" in css.lower()
