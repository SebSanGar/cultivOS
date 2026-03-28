"""Tests for the seasonal comparison chart on the field detail page."""

import pytest


@pytest.fixture
def farm_with_seasonal_data(client, db, admin_headers):
    """Create a farm with health scores in both seasons."""
    from datetime import datetime
    from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord

    farm = Farm(name="Rancho Estacional", state="Jalisco", country="MX")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    field = Field(name="Parcela Temporal", farm_id=farm.id,
                  crop_type="maiz", hectares=10)
    db.add(field)
    db.commit()
    db.refresh(field)

    # Temporal season records (Jun-Oct)
    for month in (6, 7, 8):
        db.add(HealthScore(field_id=field.id, score=75.0,
                           ndvi_mean=0.65, scored_at=datetime(2025, month, 15)))
    # Secas season records (Nov-May)
    for month in (1, 2, 3):
        db.add(HealthScore(field_id=field.id, score=60.0,
                           ndvi_mean=0.50, scored_at=datetime(2025, month, 15)))
    # Treatments in temporal
    db.add(TreatmentRecord(field_id=field.id, health_score_used=70.0,
                           problema="Estres hidrico", causa_probable="Sequia",
                           tratamiento="Compost organico", urgencia="media",
                           prevencion="Riego regular",
                           created_at=datetime(2025, 7, 1)))
    db.add(TreatmentRecord(field_id=field.id, health_score_used=72.0,
                           problema="Deficiencia nutrientes", causa_probable="Suelo pobre",
                           tratamiento="Bocashi", urgencia="baja",
                           prevencion="Rotacion de cultivos",
                           created_at=datetime(2025, 8, 1)))
    db.commit()

    return {"farm_id": farm.id, "field_id": field.id}


# ── HTML structure ──

def test_seasonal_section_in_field_html(client):
    """Field detail HTML has the Comparacion Estacional section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-seasonal"' in html
    assert "Comparacion Estacional" in html


def test_seasonal_chart_container_in_html(client):
    """Field detail HTML has a container for the seasonal chart."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="seasonal-content"' in resp.text


# ── JS logic ──

def test_field_js_has_seasonal_render(client):
    """field.js contains the renderSeasonalComparison function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderSeasonalComparison" in resp.text


def test_field_js_fetches_seasonal_comparison(client):
    """field.js fetches the /seasonal-comparison endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "/seasonal-comparison" in resp.text


# ── CSS ──

def test_seasonal_styles_present(client):
    """styles.css has seasonal comparison styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "seasonal" in css


# ── API integration ──

def test_seasonal_api_returns_both_seasons(client, farm_with_seasonal_data, admin_headers):
    """GET seasonal-comparison returns temporal and secas with correct data."""
    fid = farm_with_seasonal_data["farm_id"]
    field_id = farm_with_seasonal_data["field_id"]
    resp = client.get(
        f"/api/farms/{fid}/fields/{field_id}/seasonal-comparison"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "temporal" in data
    assert "secas" in data
    assert data["temporal"]["avg_health_score"] == 75.0
    assert data["temporal"]["treatment_count"] == 2
    assert data["secas"]["avg_health_score"] == 60.0
    assert data["secas"]["data_points"] == 3


def test_seasonal_api_handles_empty_field(client, admin_headers):
    """GET seasonal-comparison returns null scores when no data exists."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Vacio Estacional",
        "owner_name": "Test",
        "location_lat": 20.5,
        "location_lon": -103.2,
        "total_hectares": 10,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()

    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Campo Sin Datos",
        "crop_type": "frijol",
        "hectares": 5,
    }).json()

    resp = client.get(
        f"/api/farms/{farm['id']}/fields/{field['id']}/seasonal-comparison"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["temporal"]["avg_health_score"] is None
    assert data["secas"]["avg_health_score"] is None
