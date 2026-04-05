"""Tests for the treatment trust scores page at /confianza-tratamientos."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.session import get_db


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def page_client(app):
    return TestClient(app, raise_server_exceptions=False)


# --- HTML structure tests ---


def test_page_loads_200(page_client):
    """Page at /confianza-tratamientos returns 200."""
    resp = page_client.get("/confianza-tratamientos")
    assert resp.status_code == 200


def test_page_has_html_structure(page_client):
    """Page has basic HTML structure."""
    resp = page_client.get("/confianza-tratamientos")
    body = resp.text
    assert "<!DOCTYPE html>" in body
    assert '<html lang="es">' in body
    assert "Confianza en Tratamientos" in body


def test_page_has_title(page_client):
    """Page title contains cultivOS and Confianza."""
    resp = page_client.get("/confianza-tratamientos")
    assert "<title>" in resp.text
    assert "Confianza" in resp.text


def test_page_has_nav(page_client):
    """Page has navigation bar."""
    resp = page_client.get("/confianza-tratamientos")
    body = resp.text
    assert "intel-nav" in body
    assert "cultivOS" in body or "cultiv" in body


def test_page_has_stats_strip(page_client):
    """Page has stats strip with KPI cards."""
    resp = page_client.get("/confianza-tratamientos")
    body = resp.text
    assert "trust-stats" in body or "intel-stats-strip" in body
    assert "stat-total" in body
    assert "stat-feedback" in body
    assert "stat-avg-trust" in body
    assert "stat-best" in body


def test_page_has_cards_container(page_client):
    """Page has cards container for trust treatment cards."""
    resp = page_client.get("/confianza-tratamientos")
    assert "trust-cards" in resp.text


def test_page_has_crop_filter(page_client):
    """Page has crop filter dropdown."""
    resp = page_client.get("/confianza-tratamientos")
    body = resp.text
    assert "trust-crop-filter" in body
    assert "Todos los cultivos" in body


def test_page_has_subtitle(page_client):
    """Page has descriptive subtitle."""
    resp = page_client.get("/confianza-tratamientos")
    body = resp.text
    assert "retroalimentacion" in body.lower()


def test_page_loads_js(page_client):
    """Page loads the confianza-tratamientos JS file."""
    resp = page_client.get("/confianza-tratamientos")
    assert "confianza-tratamientos.js" in resp.text


def test_page_links_stylesheet(page_client):
    """Page links styles.css."""
    resp = page_client.get("/confianza-tratamientos")
    assert "styles.css" in resp.text


def test_page_has_spanish_labels(page_client):
    """Key labels are in Spanish."""
    resp = page_client.get("/confianza-tratamientos")
    body = resp.text
    assert "Tratamientos evaluados" in body
    assert "Total retroalimentaciones" in body
    assert "Confianza promedio" in body
    assert "Mejor tratamiento" in body


def test_page_has_active_nav_tab(page_client):
    """The Confianza tab is marked active."""
    resp = page_client.get("/confianza-tratamientos")
    assert 'active' in resp.text


def test_page_has_intel_body_class(page_client):
    """Page uses intel-body class for theme scoping."""
    resp = page_client.get("/confianza-tratamientos")
    assert 'class="intel-body"' in resp.text


# --- JS file tests ---


def test_js_file_loads(page_client):
    """JS file at /confianza-tratamientos.js returns 200."""
    resp = page_client.get("/confianza-tratamientos.js")
    assert resp.status_code == 200


def test_js_has_fetch_treatment_trust(page_client):
    """JS fetches /api/intel/treatment-trust endpoint."""
    resp = page_client.get("/confianza-tratamientos.js")
    assert "/api/intel/treatment-trust" in resp.text


def test_js_has_filter_function(page_client):
    """JS defines filterTrust function."""
    resp = page_client.get("/confianza-tratamientos.js")
    assert "filterTrust" in resp.text


def test_js_has_trust_color_function(page_client):
    """JS has trust color categorization."""
    resp = page_client.get("/confianza-tratamientos.js")
    assert "trustColor" in resp.text


def test_js_renders_cards(page_client):
    """JS references trust-cards container for rendering."""
    resp = page_client.get("/confianza-tratamientos.js")
    assert "trust-cards" in resp.text


def test_js_handles_empty_state(page_client):
    """JS handles empty state with message."""
    resp = page_client.get("/confianza-tratamientos.js")
    assert "No hay retroalimentacion" in resp.text


def test_js_updates_stats(page_client):
    """JS updates stat elements."""
    resp = page_client.get("/confianza-tratamientos.js")
    body = resp.text
    assert "stat-total" in body
    assert "stat-feedback" in body
    assert "stat-avg-trust" in body
    assert "stat-best" in body
