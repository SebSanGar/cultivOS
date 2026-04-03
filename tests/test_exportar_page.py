"""Tests for the data export center page at /exportar."""

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


def _seed_farms(db):
    """Seed test farms with fields."""
    f1 = Farm(name="Rancho Jalisco", state="Jalisco", total_hectares=80.0)
    f2 = Farm(name="Rancho Michoacan", state="Michoacan", total_hectares=50.0)
    db.add_all([f1, f2])
    db.commit()
    field1 = Field(name="Parcela Norte", farm_id=f1.id, crop_type="maiz", hectares=20.0)
    db.add(field1)
    db.commit()
    return f1, f2


# ── Page Load Tests ────────────────────────────────────────────


class TestExportarPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/exportar")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/exportar")
        assert "Exportar" in resp.text or "Centro de Exportacion" in resp.text

    def test_page_has_subtitle(self, client):
        resp = client.get("/exportar")
        assert "descarga" in resp.text.lower() or "exporta" in resp.text.lower()

    def test_page_has_html_structure(self, client):
        resp = client.get("/exportar")
        assert "<!DOCTYPE html>" in resp.text
        assert '<html lang="es">' in resp.text

    def test_page_has_nav(self, client):
        resp = client.get("/exportar")
        assert "intel-nav" in resp.text

    def test_page_has_footer(self, client):
        resp = client.get("/exportar")
        assert "intel-footer" in resp.text


# ── Form Elements ────────────────────────────────────────────


class TestExportarFormElements:
    """Form contains farm selector, format options, and download buttons."""

    def test_has_farm_selector(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-farm-select"' in resp.text

    def test_has_format_selector(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-format-select"' in resp.text

    def test_has_date_start(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-date-start"' in resp.text

    def test_has_date_end(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-date-end"' in resp.text

    def test_has_download_button(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-download-btn"' in resp.text

    def test_format_options_include_csv(self, client):
        resp = client.get("/exportar")
        assert "CSV" in resp.text

    def test_format_options_include_pdf(self, client):
        resp = client.get("/exportar")
        assert "PDF" in resp.text


# ── Export Categories ────────────────────────────────────────────


class TestExportarCategories:
    """Page shows available export categories."""

    def test_has_health_export_option(self, client):
        resp = client.get("/exportar")
        assert "salud" in resp.text.lower() or "health" in resp.text.lower()

    def test_has_soil_export_option(self, client):
        resp = client.get("/exportar")
        assert "suelo" in resp.text.lower() or "soil" in resp.text.lower()

    def test_has_treatment_export_option(self, client):
        resp = client.get("/exportar")
        assert "tratamiento" in resp.text.lower() or "treatment" in resp.text.lower()

    def test_has_flight_export_option(self, client):
        resp = client.get("/exportar")
        assert "vuelo" in resp.text.lower() or "flight" in resp.text.lower()

    def test_has_category_selector(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-category-select"' in resp.text


# ── Stats Strip ────────────────────────────────────────────


class TestExportarStatsStrip:
    """Stats strip shows portfolio metrics."""

    def test_has_farms_stat(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-stat-farms"' in resp.text

    def test_has_hectares_stat(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-stat-hectares"' in resp.text

    def test_has_fields_stat(self, client):
        resp = client.get("/exportar")
        assert 'id="exportar-stat-fields"' in resp.text


# ── Navigation ────────────────────────────────────────────


class TestExportarNavigation:
    """Navigation links present."""

    def test_has_home_link(self, client):
        resp = client.get("/exportar")
        assert 'href="/"' in resp.text

    def test_has_intel_link(self, client):
        resp = client.get("/exportar")
        assert 'href="/intel"' in resp.text

    def test_has_reportes_link(self, client):
        resp = client.get("/exportar")
        assert 'href="/reportes"' in resp.text


# ── API Integration ────────────────────────────────────────────


class TestExportarAPIIntegration:
    """Export APIs work correctly."""

    def test_farms_api_returns_200(self, client, db):
        _seed_farms(db)
        resp = client.get("/api/farms")
        assert resp.status_code == 200

    def test_farm_csv_export_returns_csv(self, client, db):
        f1, _ = _seed_farms(db)
        resp = client.get(f"/api/farms/{f1.id}/export?format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_farm_pdf_report_returns_pdf(self, client, db):
        f1, _ = _seed_farms(db)
        resp = client.post(f"/api/farms/{f1.id}/report")
        assert resp.status_code == 200
        assert "application/pdf" in resp.headers.get("content-type", "")

    def test_intel_export_returns_csv(self, client, db):
        _seed_farms(db)
        resp = client.get("/api/intel/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")


# ── JS Loaded ────────────────────────────────────────────


class TestExportarJSLoaded:
    """JavaScript file is loaded."""

    def test_js_script_tag(self, client):
        resp = client.get("/exportar")
        assert 'src="/exportar.js"' in resp.text

    def test_js_file_serves(self, client):
        resp = client.get("/exportar.js")
        assert resp.status_code == 200
        assert "fetchJSON" in resp.text or "fetch" in resp.text
