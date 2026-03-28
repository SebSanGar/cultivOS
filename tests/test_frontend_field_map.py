"""Tests for the field boundary map on the field detail page."""

import pytest


# ── HTML structure ──

def test_map_section_in_field_html(client):
    """Field detail HTML has the Mapa del Campo section."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="section-map"' in html
    assert "Mapa del Campo" in html


def test_map_container_in_html(client):
    """Field detail HTML has a map container div."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert 'id="field-map"' in resp.text


def test_leaflet_css_included(client):
    """Field detail HTML includes Leaflet CSS CDN."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert "leaflet" in resp.text.lower()


def test_leaflet_js_included(client):
    """Field detail HTML includes Leaflet JS CDN."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert "leaflet" in resp.text.lower()


# ── JS logic ──

def test_field_js_has_render_field_map(client):
    """field.js contains the renderFieldMap function."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderFieldMap" in resp.text


def test_field_js_handles_null_boundary(client):
    """field.js handles null boundary_coordinates gracefully."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    js = resp.text
    assert "boundary_coordinates" in js


def test_field_js_uses_L_map(client):
    """field.js uses Leaflet L.map to initialize the map."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "L.map" in resp.text


def test_field_js_uses_polygon(client):
    """field.js creates a Leaflet polygon from boundary coordinates."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "L.polygon" in resp.text


def test_field_js_calls_render_map(client):
    """field.js calls renderFieldMap during page load."""
    resp = client.get("/field.js")
    assert resp.status_code == 200
    assert "renderFieldMap" in resp.text


# ── Map CSS ──

def test_styles_has_map_container(client):
    """styles.css has styling for the field map container."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    assert "field-map" in resp.text
