"""Tests for the alert configuration page at /alertas-config."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import AlertConfig, Farm
from cultivos.db.session import get_db


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def farm(db):
    f = Farm(name="Rancho Alertas", state="Jalisco", total_hectares=30.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture()
def config(db, farm):
    c = AlertConfig(
        farm_id=farm.id,
        health_score_floor=50.0,
        ndvi_minimum=0.4,
        temp_max_c=42.0,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# --- Page load tests ---

class TestAlertConfigPageLoad:
    def test_page_returns_200(self, client):
        resp = client.get("/alertas-config")
        assert resp.status_code == 200

    def test_page_is_html(self, client):
        resp = client.get("/alertas-config")
        assert "text/html" in resp.headers["content-type"]

    def test_page_has_title(self, client):
        resp = client.get("/alertas-config")
        assert "Configuracion de Alertas" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/alertas-config")
        assert 'id="alert-farm-select"' in resp.text

    def test_page_has_health_slider(self, client):
        resp = client.get("/alertas-config")
        assert 'id="slider-health"' in resp.text

    def test_page_has_ndvi_slider(self, client):
        resp = client.get("/alertas-config")
        assert 'id="slider-ndvi"' in resp.text

    def test_page_has_temp_slider(self, client):
        resp = client.get("/alertas-config")
        assert 'id="slider-temp"' in resp.text

    def test_page_has_save_button(self, client):
        resp = client.get("/alertas-config")
        assert 'id="alert-save-btn"' in resp.text

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/alertas-config")
        text = resp.text
        assert "Salud minima" in text
        assert "NDVI minimo" in text
        assert "Temperatura maxima" in text


# --- API integration tests ---

class TestAlertConfigAPI:
    def test_get_config_returns_defaults(self, client, farm):
        resp = client.get(f"/api/farms/{farm.id}/alert-config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["health_score_floor"] == 40.0
        assert data["ndvi_minimum"] == 0.3
        assert data["temp_max_c"] == 45.0

    def test_get_config_returns_existing(self, client, farm, config):
        resp = client.get(f"/api/farms/{farm.id}/alert-config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["health_score_floor"] == 50.0
        assert data["ndvi_minimum"] == 0.4
        assert data["temp_max_c"] == 42.0

    def test_put_updates_config(self, client, farm, config):
        resp = client.put(
            f"/api/farms/{farm.id}/alert-config",
            json={"health_score_floor": 60.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["health_score_floor"] == 60.0
        # Other fields unchanged
        assert data["ndvi_minimum"] == 0.4
        assert data["temp_max_c"] == 42.0

    def test_put_creates_if_missing(self, client, farm):
        resp = client.put(
            f"/api/farms/{farm.id}/alert-config",
            json={"ndvi_minimum": 0.5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ndvi_minimum"] == 0.5
        # Defaults for other fields
        assert data["health_score_floor"] == 40.0
        assert data["temp_max_c"] == 45.0

    def test_post_creates_config(self, client, farm):
        resp = client.post(
            f"/api/farms/{farm.id}/alert-config",
            json={
                "health_score_floor": 55.0,
                "ndvi_minimum": 0.35,
                "temp_max_c": 40.0,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["health_score_floor"] == 55.0
        assert data["ndvi_minimum"] == 0.35
        assert data["temp_max_c"] == 40.0

    def test_get_config_404_for_missing_farm(self, client):
        resp = client.get("/api/farms/99999/alert-config")
        assert resp.status_code == 404


# --- Frontend HTML structure tests ---

class TestAlertConfigHTMLStructure:
    def test_has_nav(self, client):
        resp = client.get("/alertas-config")
        assert '<nav class="intel-nav">' in resp.text

    def test_has_status_message_area(self, client):
        resp = client.get("/alertas-config")
        assert 'id="alert-status"' in resp.text

    def test_has_current_config_display(self, client):
        resp = client.get("/alertas-config")
        assert 'id="alert-current"' in resp.text

    def test_links_styles_css(self, client):
        resp = client.get("/alertas-config")
        assert 'href="/styles.css"' in resp.text

    def test_links_js_file(self, client):
        resp = client.get("/alertas-config")
        assert 'src="/alert-config.js"' in resp.text
