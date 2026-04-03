"""Tests for the executive portfolio summary page at /resumen."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field
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


def _seed_portfolio(db):
    """Seed farms and fields for portfolio summary testing."""
    farm1 = Farm(
        name="Rancho El Sol", state="Jalisco", total_hectares=100.0,
        location_lat=20.6597, location_lon=-103.3496, municipality="Zapopan"
    )
    farm2 = Farm(
        name="Rancho La Luna", state="Jalisco", total_hectares=60.0,
        location_lat=20.7200, location_lon=-103.4000, municipality="Tlajomulco"
    )
    db.add_all([farm1, farm2])
    db.flush()
    f1 = Field(farm_id=farm1.id, name="Parcela Norte", hectares=50.0, crop_type="maiz")
    f2 = Field(farm_id=farm1.id, name="Parcela Sur", hectares=50.0, crop_type="agave")
    f3 = Field(farm_id=farm2.id, name="Parcela Central", hectares=60.0, crop_type="aguacate")
    db.add_all([f1, f2, f3])
    db.commit()
    return farm1, farm2


# -- Page Load Tests --


class TestResumenPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/resumen")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/resumen")
        assert "Resumen Ejecutivo" in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/resumen")
        assert "intel-nav" in resp.text

    def test_page_has_script(self, client):
        resp = client.get("/resumen")
        assert "resumen.js" in resp.text

    def test_page_has_footer(self, client):
        resp = client.get("/resumen")
        assert "cultivos-footer" in resp.text

    def test_page_has_fodecijal_reference(self, client):
        resp = client.get("/resumen")
        assert "FODECIJAL" in resp.text


# -- KPI Strip Tests --


class TestResumenKPIStrip:
    """KPI stat cards render for executive summary."""

    def test_kpi_strip_exists(self, client):
        resp = client.get("/resumen")
        assert 'id="resumen-kpis"' in resp.text

    def test_kpi_farms(self, client):
        resp = client.get("/resumen")
        assert 'id="kpi-farms"' in resp.text

    def test_kpi_fields(self, client):
        resp = client.get("/resumen")
        assert 'id="kpi-fields"' in resp.text

    def test_kpi_hectares(self, client):
        resp = client.get("/resumen")
        assert 'id="kpi-hectares"' in resp.text

    def test_kpi_health(self, client):
        resp = client.get("/resumen")
        assert 'id="kpi-health"' in resp.text

    def test_kpi_savings(self, client):
        resp = client.get("/resumen")
        assert 'id="kpi-savings"' in resp.text

    def test_kpi_roi(self, client):
        resp = client.get("/resumen")
        assert 'id="kpi-roi"' in resp.text

    def test_kpi_spanish_labels(self, client):
        resp = client.get("/resumen")
        text = resp.text
        assert "Granjas" in text
        assert "Campos" in text
        assert "Hectareas Totales" in text
        assert "Salud Promedio" in text
        assert "Ahorro Total" in text
        assert "ROI Proyectado" in text


# -- Chart & Table DOM Tests --


class TestResumenChartsAndTables:
    """Charts and portfolio table exist for JS rendering."""

    def test_health_distribution_chart(self, client):
        resp = client.get("/resumen")
        assert 'id="resumen-health-dist"' in resp.text

    def test_savings_chart(self, client):
        resp = client.get("/resumen")
        assert 'id="resumen-savings-chart"' in resp.text

    def test_roi_projection_chart(self, client):
        resp = client.get("/resumen")
        assert 'id="resumen-roi-chart"' in resp.text

    def test_portfolio_table_exists(self, client):
        resp = client.get("/resumen")
        assert 'id="resumen-table"' in resp.text

    def test_portfolio_table_headers(self, client):
        resp = client.get("/resumen")
        text = resp.text
        assert "Granja" in text
        assert "Municipio" in text
        assert "Hectareas" in text
        assert "Salud" in text

    def test_farm_count_badge(self, client):
        resp = client.get("/resumen")
        assert 'id="resumen-farm-count"' in resp.text

    def test_export_button_exists(self, client):
        resp = client.get("/resumen")
        assert "Exportar CSV" in resp.text

    def test_chart_panel_titles(self, client):
        resp = client.get("/resumen")
        text = resp.text
        assert "Distribucion de Salud" in text
        assert "Desglose de Ahorro" in text
        assert "Proyeccion de Retorno" in text


# -- API Integration Tests --


class TestResumenAPIIntegration:
    """API endpoints return data needed for executive summary."""

    def test_farms_list_returns_200(self, client, db):
        _seed_portfolio(db)
        resp = client.get("/api/farms")
        assert resp.status_code == 200

    def test_farms_have_hectares(self, client, db):
        _seed_portfolio(db)
        resp = client.get("/api/farms")
        data = resp.json()
        farms = data["data"]
        assert all(f.get("total_hectares") is not None for f in farms)

    def test_fields_available_per_farm(self, client, db):
        farm1, _ = _seed_portfolio(db)
        resp = client.get(f"/api/farms/{farm1.id}/fields")
        assert resp.status_code == 200
        fields = resp.json()
        assert len(fields) >= 2
