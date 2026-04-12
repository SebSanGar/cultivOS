"""Tests for the field soil nutrient trajectory page at /nutrientes-suelo (#221)."""

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
def client(app):
    return TestClient(app, raise_server_exceptions=False)


class TestSoilNutrientsPage:
    def test_page_returns_200(self, client):
        resp = client.get("/nutrientes-suelo")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/nutrientes-suelo")
        assert "Nutrientes" in resp.text or "Suelo" in resp.text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/nutrientes-suelo")
        assert 'id="sn-farm-select"' in resp.text

    def test_page_has_field_selector(self, client):
        resp = client.get("/nutrientes-suelo")
        assert 'id="sn-field-select"' in resp.text

    def test_page_has_chart_canvas(self, client):
        resp = client.get("/nutrientes-suelo")
        assert 'id="sn-chart"' in resp.text

    def test_page_has_trend_pills(self, client):
        resp = client.get("/nutrientes-suelo")
        html = resp.text
        assert 'id="sn-nitrogen-trend"' in html
        assert 'id="sn-phosphorus-trend"' in html
        assert 'id="sn-potassium-trend"' in html
        assert 'id="sn-organic-trend"' in html

    def test_page_includes_chartjs(self, client):
        resp = client.get("/nutrientes-suelo")
        assert "chart.js" in resp.text.lower() or "chart.umd" in resp.text.lower()

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/nutrientes-suelo")
        html = resp.text
        assert "Finca" in html
        assert "Parcela" in html or "Campo" in html
        assert "Nitr" in html  # Nitrógeno
        assert "Fósforo" in html or "Fosforo" in html
        assert "Potasio" in html

    def test_page_includes_js_script(self, client):
        resp = client.get("/nutrientes-suelo")
        assert "nutrientes-suelo.js" in resp.text

    def test_page_references_soil_nutrients_endpoint(self, client):
        resp = client.get("/nutrientes-suelo.js")
        assert "/soil-nutrients" in resp.text
