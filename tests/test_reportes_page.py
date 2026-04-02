"""Tests for the portfolio report generation page at /reportes."""

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm
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
    """Seed test farms for multi-select."""
    f1 = Farm(name="Rancho Jalisco", state="Jalisco", total_hectares=80.0)
    f2 = Farm(name="Rancho Michoacan", state="Michoacan", total_hectares=50.0)
    db.add_all([f1, f2])
    db.commit()
    return f1, f2


# ── Page Load Tests ────────────────────────────────────────────


class TestReportesPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/reportes")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/reportes")
        assert "Reportes" in resp.text

    def test_page_has_subtitle(self, client):
        resp = client.get("/reportes")
        assert "portafolio" in resp.text.lower() or "reporte" in resp.text.lower()


# ── Form Elements ────────────────────────────────────────────


class TestReportesFormElements:
    """Form contains farm multi-select, date range, and generate button."""

    def test_has_farm_selector(self, client):
        resp = client.get("/reportes")
        assert 'id="reportes-farm-select"' in resp.text

    def test_has_date_start(self, client):
        resp = client.get("/reportes")
        assert 'id="reportes-date-start"' in resp.text

    def test_has_date_end(self, client):
        resp = client.get("/reportes")
        assert 'id="reportes-date-end"' in resp.text

    def test_has_generate_button(self, client):
        resp = client.get("/reportes")
        assert 'id="reportes-generate-btn"' in resp.text

    def test_has_download_section(self, client):
        resp = client.get("/reportes")
        assert 'id="reportes-download"' in resp.text


# ── Stats Strip ────────────────────────────────────────────


class TestReportesStatsStrip:
    """Stats strip shows key portfolio metrics."""

    def test_has_stats_strip(self, client):
        resp = client.get("/reportes")
        assert 'id="reportes-stat-farms"' in resp.text

    def test_has_hectares_stat(self, client):
        resp = client.get("/reportes")
        assert 'id="reportes-stat-hectares"' in resp.text


# ── Navigation ────────────────────────────────────────────


class TestReportesNavigation:
    """Navigation elements are present."""

    def test_has_nav(self, client):
        resp = client.get("/reportes")
        assert "nav" in resp.text.lower()

    def test_has_home_link(self, client):
        resp = client.get("/reportes")
        assert 'href="/"' in resp.text


# ── API Integration ────────────────────────────────────────────


class TestReportesAPIIntegration:
    """Backend API endpoints work with the page."""

    def test_farms_api_returns_list(self, client, db):
        _seed_farms(db)
        resp = client.get("/api/farms")
        assert resp.status_code == 200

    def test_portfolio_report_api_returns_pdf(self, client, db):
        _seed_farms(db)
        resp = client.post("/api/reports/portfolio")
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "application/pdf"


# ── JS Script ────────────────────────────────────────────


class TestReportesJSLoaded:
    """JavaScript file is referenced."""

    def test_js_script_tag(self, client):
        resp = client.get("/reportes")
        assert "reportes.js" in resp.text
