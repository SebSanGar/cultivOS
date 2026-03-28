"""Tests for the crop rotation suggestion widget on the field detail page."""

import pytest
from cultivos.db.models import Farm, Field


@pytest.fixture
def farm_with_crop(db):
    """Farm with a field that has a crop_type set."""
    farm = Farm(name="Rancho Rotacion", state="Jalisco", total_hectares=30)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Maiz", crop_type="maiz", hectares=10)
    db.add(field)
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


@pytest.fixture
def farm_no_crop(db):
    """Farm with a field that has no crop_type."""
    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=5)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Sin Cultivo", crop_type=None, hectares=5)
    db.add(field)
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


# -- API integration --

def test_rotation_returns_plan_with_crop(client, farm_with_crop):
    """GET /rotation returns a rotation plan when field has a crop_type."""
    fid = farm_with_crop["farm_id"]
    field_id = farm_with_crop["field_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/rotation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_id"] == field_id
    assert data["last_crop"] == "maiz"
    assert len(data["plan"]) > 0
    entry = data["plan"][0]
    assert "season" in entry
    assert "crop" in entry
    assert "reason" in entry
    assert "purpose" in entry
    assert "months" in entry


def test_rotation_handles_no_crop(client, farm_no_crop):
    """GET /rotation returns 422 when field has no crop_type."""
    fid = farm_no_crop["farm_id"]
    field_id = farm_no_crop["field_id"]
    resp = client.get(f"/api/farms/{fid}/fields/{field_id}/rotation")
    assert resp.status_code == 422


def test_rotation_404_bad_farm(client):
    """GET /rotation returns 404 for nonexistent farm."""
    resp = client.get("/api/farms/9999/fields/1/rotation")
    assert resp.status_code == 404


def test_rotation_404_bad_field(client, farm_with_crop):
    """GET /rotation returns 404 for nonexistent field."""
    fid = farm_with_crop["farm_id"]
    resp = client.get(f"/api/farms/{fid}/fields/9999/rotation")
    assert resp.status_code == 404


# -- HTML structure --

def test_rotation_section_in_field_html(client):
    """Field detail HTML has the rotation widget section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="rotation-content"' in resp.text


def test_rotation_section_has_title(client):
    """Field detail HTML has the section title."""
    resp = client.get("/campo")
    assert "Plan de Rotacion" in resp.text


# -- Frontend JS: property name fix and enhanced rendering --

def test_field_js_uses_plan_not_seasons(client):
    """field.js uses rotation.plan (matching API), not rotation.seasons."""
    resp = client.get("/field.js")
    js = resp.text
    assert "rotation.plan" in js or ".plan" in js
    # Should NOT use the old broken property name
    assert "rotation.seasons" not in js


def test_field_js_has_render_rotation(client):
    """field.js contains the renderRotation function."""
    resp = client.get("/field.js")
    assert "renderRotation" in resp.text


def test_field_js_shows_last_crop(client):
    """field.js renders the last_crop field (current crop)."""
    resp = client.get("/field.js")
    assert "last_crop" in resp.text


def test_field_js_shows_purpose(client):
    """field.js renders the purpose field (rotation benefit)."""
    resp = client.get("/field.js")
    assert "purpose" in resp.text


def test_field_js_shows_months(client):
    """field.js renders the months field (season timing)."""
    resp = client.get("/field.js")
    js = resp.text
    assert "months" in js
