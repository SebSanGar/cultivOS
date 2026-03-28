"""Tests for the soil analysis data entry form on the field detail page.

Tests cover:
1. Form HTML exists in field.html
2. POST /api/farms/{id}/fields/{id}/soil creates a record and returns 201
3. POST with invalid data returns 422
4. New record appears in GET list after creation
5. Form JS handler exists in field.js
"""

import pytest
from datetime import datetime
from cultivos.db.models import Farm, Field, SoilAnalysis


@pytest.fixture
def field_for_soil(db):
    """Farm with a field ready for soil data entry."""
    farm = Farm(name="Rancho Entrada", state="Jalisco", total_hectares=30)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Suelo", crop_type="maiz", hectares=10)
    db.add(field)
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


@pytest.fixture
def field_with_existing_soil(db):
    """Farm with a field that already has one soil record."""
    farm = Farm(name="Rancho Existente", state="Jalisco", total_hectares=20)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Con Datos", crop_type="aguacate", hectares=8)
    db.add(field)
    db.flush()
    db.add(SoilAnalysis(
        field_id=field.id, ph=6.5, organic_matter_pct=3.0,
        nitrogen_ppm=30, phosphorus_ppm=20, potassium_ppm=150,
        texture="franco", moisture_pct=25.0, depth_cm=30,
        sampled_at=datetime(2026, 3, 1),
    ))
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


# -- API tests: POST creates a soil record --

def test_create_soil_analysis_returns_201(client, field_for_soil):
    """POST /api/farms/{id}/fields/{id}/soil creates a record."""
    fid = field_for_soil["farm_id"]
    field_id = field_for_soil["field_id"]
    payload = {
        "ph": 6.8,
        "organic_matter_pct": 3.5,
        "nitrogen_ppm": 35,
        "phosphorus_ppm": 22,
        "potassium_ppm": 180,
        "texture": "franco-arcilloso",
        "moisture_pct": 28.0,
        "depth_cm": 30,
        "sampled_at": "2026-03-28T10:00:00",
    }
    resp = client.post(f"/api/farms/{fid}/fields/{field_id}/soil", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ph"] == 6.8
    assert data["organic_matter_pct"] == 3.5
    assert data["texture"] == "franco-arcilloso"
    assert data["field_id"] == field_id
    assert data["id"] is not None


def test_create_soil_minimal_fields(client, field_for_soil):
    """POST with only required field (sampled_at) succeeds."""
    fid = field_for_soil["farm_id"]
    field_id = field_for_soil["field_id"]
    payload = {"sampled_at": "2026-03-28T12:00:00"}
    resp = client.post(f"/api/farms/{fid}/fields/{field_id}/soil", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ph"] is None
    assert data["nitrogen_ppm"] is None


def test_create_soil_invalid_ph_rejected(client, field_for_soil):
    """POST with pH > 14 returns 422."""
    fid = field_for_soil["farm_id"]
    field_id = field_for_soil["field_id"]
    payload = {"ph": 15.0, "sampled_at": "2026-03-28T10:00:00"}
    resp = client.post(f"/api/farms/{fid}/fields/{field_id}/soil", json=payload)
    assert resp.status_code == 422


def test_create_soil_invalid_farm_returns_404(client, field_for_soil):
    """POST to nonexistent farm returns 404."""
    field_id = field_for_soil["field_id"]
    payload = {"ph": 6.5, "sampled_at": "2026-03-28T10:00:00"}
    resp = client.post(f"/api/farms/9999/fields/{field_id}/soil", json=payload)
    assert resp.status_code == 404


def test_new_record_appears_in_list(client, field_for_soil):
    """After POST, new record appears in GET list."""
    fid = field_for_soil["farm_id"]
    field_id = field_for_soil["field_id"]

    # Initially empty
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/soil")
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    # Create
    payload = {
        "ph": 7.0,
        "organic_matter_pct": 2.0,
        "sampled_at": "2026-03-28T10:00:00",
    }
    client.post(f"/api/farms/{fid}/fields/{field_id}/soil", json=payload)

    # Now list has 1 record
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/soil")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["ph"] == 7.0


def test_new_record_added_to_existing_list(client, field_with_existing_soil):
    """POST adds to existing records, not replacing them."""
    fid = field_with_existing_soil["farm_id"]
    field_id = field_with_existing_soil["field_id"]

    # Has 1 existing
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/soil")
    assert len(resp.json()) == 1

    # Add another
    payload = {
        "ph": 7.2,
        "organic_matter_pct": 3.8,
        "sampled_at": "2026-03-28T14:00:00",
    }
    client.post(f"/api/farms/{fid}/fields/{field_id}/soil", json=payload)

    # Now has 2
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/soil")
    assert len(resp.json()) == 2


# -- Frontend tests: HTML and JS contain form elements --

def test_field_html_contains_soil_form(client):
    """field.html contains the soil data entry form section."""
    resp = client.get("/field.html")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="soil-entry-form"' in html
    assert 'id="soil-ph"' in html
    assert 'id="soil-sampled-at"' in html


def test_field_html_form_has_submit_button(client):
    """field.html form has a submit button."""
    resp = client.get("/field.html")
    html = resp.text
    assert 'id="soil-submit-btn"' in html


def test_field_js_has_submit_handler(client):
    """field.js contains the soil form submission handler."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "submitSoilForm" in js or "handleSoilSubmit" in js or "soil-submit-btn" in js
