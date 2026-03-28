"""Tests for the intervention scores panel on the field detail page."""

import pytest


# ── HTML structure ──

def test_intervention_section_in_field_html(client):
    """Field detail HTML has the Intervenciones Prioritarias section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-interventions"' in html
    assert "Intervenciones Prioritarias" in html


def test_intervention_container_in_html(client):
    """Field detail HTML has a container for intervention score content."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="interventions-content"' in resp.text


# ── JS logic ──

def test_field_js_has_intervention_render(client):
    """field.js contains the renderInterventionScores function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderInterventionScores" in resp.text


def test_field_js_fetches_intervention_scores(client):
    """field.js fetches the /intervention-scores endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "/intervention-scores" in resp.text


def test_field_js_shows_score_and_probability(client):
    """field.js renders intervention_score and success_probability."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "intervention_score" in js
    assert "success_probability" in js


def test_field_js_shows_cost_per_hectare(client):
    """field.js renders cost_per_hectare."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "cost_per_hectare" in js if (js := resp.text) else False


def test_field_js_handles_empty_interventions(client):
    """field.js has a placeholder for when no interventions exist."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "Sin intervenciones" in resp.text


# ── CSS ──

def test_intervention_styles_present(client):
    """styles.css has intervention score styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    assert "intervention" in resp.text


# ── API integration ──

def test_intervention_api_returns_empty_for_no_treatments(client, admin_headers):
    """GET intervention-scores returns empty list when no treatments exist."""
    resp = client.post("/api/farms", json={
        "name": "Rancho Intervencion",
        "location_lat": 20.6,
        "location_lon": -103.3,
        "total_hectares": 50,
    }, headers=admin_headers)
    assert resp.status_code == 201
    farm_id = resp.json()["id"]

    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Score",
        "crop_type": "maiz",
        "hectares": 5.0,
    }, headers=admin_headers)
    assert resp.status_code == 201
    field_id = resp.json()["id"]

    resp = client.get(
        f"/api/farms/{farm_id}/fields/{field_id}/intervention-scores",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []
