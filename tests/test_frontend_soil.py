"""Tests for the soil analysis panel on the field detail page."""

import pytest


# ── HTML structure ──

def test_soil_section_in_field_html(client):
    """Field detail HTML has the Analisis de Suelo section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-soil"' in html
    assert "Analisis de Suelo" in html


def test_soil_content_container(client):
    """Field detail HTML has a container for soil content."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="soil-content"' in resp.text


def test_soil_placeholder_when_no_data(client):
    """Field detail HTML shows placeholder when no soil data."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert "Sin analisis de suelo" in resp.text


# ── JS logic ──

def test_field_js_has_render_soil(client):
    """field.js contains the renderSoil function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderSoil" in resp.text


def test_field_js_fetches_soil(client):
    """field.js fetches the /soil endpoint in Promise.all."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "/soil" in resp.text


def test_field_js_shows_ph_with_color(client):
    """field.js applies health-badge color coding to pH."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "soil.ph" in js
    assert "health-badge" in js


def test_field_js_shows_nitrogen_with_color(client):
    """field.js applies color coding to nitrogen levels."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "nitrogen_ppm" in js
    # Variable name for nitrogen color class
    assert " nCls" in js or "nCls " in js or "nCls}" in js


def test_field_js_shows_phosphorus_with_color(client):
    """field.js applies color coding to phosphorus levels."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "phosphorus_ppm" in js
    assert " pCls" in js or "pCls " in js or "pCls}" in js


def test_field_js_shows_potassium_with_color(client):
    """field.js applies color coding to potassium levels."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "potassium_ppm" in js
    # Must be standalone kCls, not substring of riskCls
    assert "${kCls}" in js


def test_field_js_shows_organic_matter_with_color(client):
    """field.js applies color coding to organic matter percentage."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "organic_matter_pct" in js
    assert "omCls" in js


def test_field_js_shows_recommendations(client):
    """field.js renders soil recommendations when present."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "soil.recommendations" in js
    assert "Recomendaciones" in js
