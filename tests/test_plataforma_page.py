"""Tests for the platform overview page at /plataforma."""

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


# -- Page Load Tests --


class TestPlataformaPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/plataforma")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/plataforma")
        assert "Plataforma cultivOS" in resp.text

    def test_page_has_body_class(self, client):
        resp = client.get("/plataforma")
        assert 'class="intel-body"' in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/plataforma")
        assert "intel-nav" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/plataforma")
        assert 'id="platform-stats"' in resp.text

    def test_page_has_category_grid(self, client):
        resp = client.get("/plataforma")
        assert 'id="category-grid"' in resp.text

    def test_page_has_search_input(self, client):
        resp = client.get("/plataforma")
        assert 'id="search-input"' in resp.text


# -- Category Tests --


class TestPlataformaCategorias:
    """Page shows all feature categories."""

    def test_has_inteligencia_category(self, client):
        resp = client.get("/plataforma")
        assert "Inteligencia Cerebro" in resp.text

    def test_has_cultivos_category(self, client):
        resp = client.get("/plataforma")
        assert "Cultivos y Suelo" in resp.text

    def test_has_drone_category(self, client):
        resp = client.get("/plataforma")
        assert "Drone y Mapas" in resp.text

    def test_has_alertas_category(self, client):
        resp = client.get("/plataforma")
        assert "Alertas y Clima" in resp.text

    def test_has_reportes_category(self, client):
        resp = client.get("/plataforma")
        assert "Reportes y Datos" in resp.text

    def test_has_operaciones_category(self, client):
        resp = client.get("/plataforma")
        assert "Operaciones" in resp.text


# -- Page Link Tests --


class TestPlataformaPageLinks:
    """Page contains links to key platform pages."""

    def test_has_link_to_intel(self, client):
        resp = client.get("/plataforma")
        assert 'href="/intel"' in resp.text

    def test_has_link_to_mapa(self, client):
        resp = client.get("/plataforma")
        assert 'href="/mapa"' in resp.text

    def test_has_link_to_regenerativo(self, client):
        resp = client.get("/plataforma")
        assert 'href="/regenerativo"' in resp.text

    def test_has_link_to_carbono(self, client):
        resp = client.get("/plataforma")
        assert 'href="/carbono"' in resp.text

    def test_has_link_to_tek(self, client):
        resp = client.get("/plataforma")
        assert 'href="/tek"' in resp.text

    def test_has_link_to_rendimiento(self, client):
        resp = client.get("/plataforma")
        assert 'href="/rendimiento"' in resp.text

    def test_has_link_to_riego(self, client):
        resp = client.get("/plataforma")
        assert 'href="/riego"' in resp.text

    def test_has_link_to_flota(self, client):
        resp = client.get("/plataforma")
        assert 'href="/flota"' in resp.text

    def test_has_link_to_exportar(self, client):
        resp = client.get("/plataforma")
        assert 'href="/exportar"' in resp.text

    def test_has_link_to_clima(self, client):
        resp = client.get("/plataforma")
        assert 'href="/clima"' in resp.text

    def test_has_link_to_whatsapp_demo(self, client):
        resp = client.get("/plataforma")
        assert 'href="/whatsapp-demo"' in resp.text

    def test_has_link_to_enfermedades(self, client):
        resp = client.get("/plataforma")
        assert 'href="/enfermedades"' in resp.text

    def test_has_link_to_anomalias(self, client):
        resp = client.get("/plataforma")
        assert 'href="/anomalias"' in resp.text

    def test_has_link_to_microbioma(self, client):
        resp = client.get("/plataforma")
        assert 'href="/microbioma"' in resp.text

    def test_has_link_to_calendario(self, client):
        resp = client.get("/plataforma")
        assert 'href="/calendario"' in resp.text

    def test_has_link_to_acciones(self, client):
        resp = client.get("/plataforma")
        assert 'href="/acciones"' in resp.text

    def test_has_link_to_regional(self, client):
        resp = client.get("/plataforma")
        assert 'href="/regional"' in resp.text


# -- Stats Strip Tests --


class TestPlataformaStats:
    """Stats strip shows platform metrics."""

    def test_has_pages_stat(self, client):
        resp = client.get("/plataforma")
        assert 'id="stat-pages"' in resp.text

    def test_has_endpoints_stat(self, client):
        resp = client.get("/plataforma")
        assert 'id="stat-endpoints"' in resp.text

    def test_has_tests_stat(self, client):
        resp = client.get("/plataforma")
        assert 'id="stat-tests"' in resp.text

    def test_has_data_sources_stat(self, client):
        resp = client.get("/plataforma")
        assert 'id="stat-sources"' in resp.text


# -- JavaScript Tests --


class TestPlataformaJS:
    """Page loads JavaScript for filtering and interactivity."""

    def test_page_loads_js(self, client):
        resp = client.get("/plataforma")
        assert 'src="/plataforma.js"' in resp.text

    def test_js_file_returns_200(self, client):
        resp = client.get("/plataforma.js")
        assert resp.status_code == 200

    def test_js_has_filter_function(self, client):
        resp = client.get("/plataforma.js")
        assert "filterPages" in resp.text

    def test_js_has_search_handler(self, client):
        resp = client.get("/plataforma.js")
        assert "search-input" in resp.text


# -- Spanish Content Tests --


class TestPlataformaSpanish:
    """All user-facing text is in Spanish."""

    def test_description_in_spanish(self, client):
        resp = client.get("/plataforma")
        assert "Vista general" in resp.text

    def test_category_filter_label(self, client):
        resp = client.get("/plataforma")
        assert "Filtrar" in resp.text or "Buscar" in resp.text

    def test_page_descriptions_in_spanish(self, client):
        resp = client.get("/plataforma")
        # Check a few page descriptions are Spanish
        assert "salud" in resp.text.lower() or "cultivo" in resp.text.lower()
