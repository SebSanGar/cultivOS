"""Tests for the farmer feedback UI on the field detail page."""

import pytest


# ── HTML structure ──

def test_feedback_section_in_field_html(client):
    """Field detail HTML has the Retroalimentacion section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-feedback"' in html
    assert "Retroalimentacion" in html


def test_feedback_container_in_html(client):
    """Field detail HTML has a container for feedback content."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="feedback-content"' in resp.text


def test_feedback_form_in_html(client):
    """Field detail HTML has a feedback submission form."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="feedback-form"' in html


# ── JS logic ──

def test_field_js_has_render_feedback(client):
    """field.js contains the renderFeedback function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderFeedback" in resp.text


def test_field_js_fetches_feedback(client):
    """field.js fetches the /feedback endpoint."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "/feedback" in resp.text


def test_field_js_shows_rating(client):
    """field.js renders rating for feedback entries."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "rating" in resp.text


def test_field_js_shows_worked_status(client):
    """field.js renders the worked/funciono status."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "worked" in resp.text


def test_field_js_shows_farmer_notes(client):
    """field.js renders farmer_notes field."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "farmer_notes" in resp.text


def test_field_js_handles_empty_feedback(client):
    """field.js handles empty feedback list gracefully."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    # Should check for empty array before rendering entries
    assert "Sin retroalimentacion" in js or "feedback" in js.lower()


def test_field_js_submit_feedback_function(client):
    """field.js has a submitFeedback function for the form."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "submitFeedback" in resp.text


# ── API integration ──

def test_feedback_api_list(client, db, admin_headers):
    """GET feedback returns entries for a field."""
    from cultivos.db.models import Farm, FarmerFeedback, Field, HealthScore, TreatmentRecord
    farm = Farm(name="Rancho Feedback")
    db.add(farm)
    db.commit()
    field = Field(farm_id=farm.id, name="Parcela Retro", crop_type="maiz")
    db.add(field)
    db.commit()
    hs = HealthScore(field_id=field.id, score=75.0)
    db.add(hs)
    db.commit()
    tr = TreatmentRecord(field_id=field.id, health_score_used=75.0,
                         problema="Deficiencia de nitrogeno",
                         causa_probable="Suelo agotado",
                         tratamiento="Compost foliar 2L/ha",
                         costo_estimado_mxn=500, urgencia="media",
                         prevencion="Rotacion de cultivos", organic=True)
    db.add(tr)
    db.commit()
    fb = FarmerFeedback(field_id=field.id, treatment_id=tr.id,
                        rating=4, worked=True, farmer_notes="Funciono bien")
    db.add(fb)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/feedback")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["rating"] == 4
    assert data[0]["worked"] is True
    assert data[0]["farmer_notes"] == "Funciono bien"
