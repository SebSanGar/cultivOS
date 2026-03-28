"""Tests for the regenerative score card on the field detail page."""

import pytest
from datetime import datetime

from cultivos.db.models import Farm, Field, TreatmentRecord


@pytest.fixture
def farm_with_treatments(db):
    """Create a farm with a field that has organic treatment data."""
    farm = Farm(name="Rancho Regenerativo", state="Jalisco", total_hectares=20)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Regen", crop_type="maiz", hectares=10)
    db.add(field)
    db.flush()

    # Add organic treatments
    db.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=65.0,
        problema="Baja fertilidad",
        causa_probable="suelo pobre",
        tratamiento="Composta enriquecida",
        urgencia="media",
        prevencion="rotacion",
        organic=True,
        costo_estimado_mxn=500,
    ))
    db.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=70.0,
        problema="Plagas",
        causa_probable="humedad",
        tratamiento="Extracto de neem",
        urgencia="media",
        prevencion="control biologico",
        organic=True,
        ancestral_method_name="Neem tradicional",
        costo_estimado_mxn=300,
    ))
    db.commit()

    return {"farm_id": farm.id, "field_id": field.id}


# -- HTML structure --

def test_regenerative_section_present_in_html(client):
    """Field detail HTML has the Puntuacion Regenerativa section container."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-regenerative"' in html
    assert "Puntuacion Regenerativa" in html


def test_regenerative_content_container(client):
    """Field detail HTML has the regenerative content div."""
    resp = client.get("/campo")
    html = resp.text
    assert 'id="regenerative-content"' in html


# -- API integration --

def test_regenerative_score_endpoint(client, farm_with_treatments, admin_headers):
    """GET /regenerative-score returns score with breakdown."""
    fid = farm_with_treatments["farm_id"]
    fld = farm_with_treatments["field_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{fld}/regenerative-score")
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "breakdown" in data
    assert "recommendations" in data
    assert data["breakdown"]["organic_treatments"] > 0


# -- Frontend JS --

def test_field_js_has_regenerative_render(client):
    """field.js contains the renderRegenerativeScore function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "renderRegenerativeScore" in js


def test_field_js_fetches_regenerative_score(client):
    """field.js fetches the /regenerative-score endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "/regenerative-score" in js


# -- CSS --

def test_regenerative_styles_present(client):
    """styles.css has regenerative card styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "regen" in css.lower()
