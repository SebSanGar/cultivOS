"""Tests for the treatment history timeline on the field detail page."""

import pytest


# ── HTML structure ──

def test_treatment_history_section_in_html(client):
    """Field detail HTML has the Historial de Tratamientos section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-treatment-history"' in html
    assert "Historial de Tratamientos" in html


def test_treatment_history_content_container(client):
    """Field detail HTML has a container for treatment history content."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="treatment-history-content"' in resp.text


def test_treatment_history_placeholder(client):
    """Field detail HTML shows placeholder when no treatment history."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert "Sin historial de tratamientos" in resp.text


# ── JS logic ──

def test_field_js_has_render_treatment_history(client):
    """field.js contains the renderTreatmentHistory function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderTreatmentHistory" in resp.text


def test_field_js_fetches_treatment_history(client):
    """field.js fetches the /treatment-history endpoint in Promise.all."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "treatment-history" in resp.text


def test_field_js_shows_applied_date(client):
    """field.js displays the applied_at date for timeline entries."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "applied_at" in js


def test_field_js_shows_organic_badge(client):
    """field.js displays an organic badge for organic treatments."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    # Should have the organic badge class or text
    assert "organic" in js.lower()
    assert "rganico" in js or "Organico" in js  # Spanish label


def test_field_js_shows_treatment_problema(client):
    """field.js displays the problema field in timeline entries."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "t.problema" in js or "entry.problema" in js or "h.problema" in js


def test_field_js_shows_treatment_urgencia(client):
    """field.js displays urgencia badge in timeline entries."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "urgencia" in js


def test_field_js_handles_empty_treatment_history(client):
    """field.js handles empty treatment history gracefully."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    # Should check for empty/null and show placeholder
    assert "Sin historial" in js or "sin historial" in js


# ── API ──

def test_treatment_history_endpoint_returns_list(client, admin_headers):
    """GET treatment-history returns empty list for field with no applied treatments."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Timeline",
        "owner_name": "Owner",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 20,
        "municipality": "Zapopan",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()
    field = client.post(f"/api/farms/{farm['id']}/fields", json={
        "name": "Parcela Timeline",
        "crop_type": "maiz",
        "hectares": 10,
    }).json()
    resp = client.get(f"/api/farms/{farm['id']}/fields/{field['id']}/treatments/treatment-history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_treatment_timeline_model_has_organic(client, admin_headers):
    """TreatmentTimelineEntry includes organic field for badge display."""
    from cultivos.models.treatment import TreatmentTimelineEntry
    fields = TreatmentTimelineEntry.model_fields
    assert "organic" in fields, "TreatmentTimelineEntry must include 'organic' for badge display"
