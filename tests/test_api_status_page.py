"""Tests for /api-status frontend page — system health dashboard."""

import pytest


class TestApiStatusPage:
    """Tests for the API status dashboard page."""

    def test_page_loads(self, client):
        resp = client.get("/api-status")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        html = client.get("/api-status").text
        assert "Estado del Sistema" in html

    def test_page_has_status_indicator(self, client):
        html = client.get("/api-status").text
        assert 'id="system-status"' in html

    def test_page_has_version_display(self, client):
        html = client.get("/api-status").text
        assert 'id="api-version"' in html

    def test_page_has_python_version(self, client):
        html = client.get("/api-status").text
        assert 'id="python-version"' in html

    def test_page_has_uptime_display(self, client):
        html = client.get("/api-status").text
        assert 'id="uptime"' in html

    def test_page_has_db_counts_section(self, client):
        html = client.get("/api-status").text
        assert 'id="db-counts"' in html

    def test_page_has_endpoint_count(self, client):
        html = client.get("/api-status").text
        assert 'id="endpoint-count"' in html

    def test_page_has_test_count(self, client):
        html = client.get("/api-status").text
        assert 'id="test-count"' in html

    def test_page_has_latest_data_section(self, client):
        html = client.get("/api-status").text
        assert 'id="latest-data"' in html

    def test_page_has_stats_strip(self, client):
        html = client.get("/api-status").text
        assert "stats-strip" in html

    def test_page_has_refresh_button(self, client):
        html = client.get("/api-status").text
        assert 'id="refresh-btn"' in html

    def test_page_has_script(self, client):
        html = client.get("/api-status").text
        assert "api-status.js" in html

    def test_page_has_stylesheet(self, client):
        html = client.get("/api-status").text
        assert "styles.css" in html

    def test_page_has_nav_back(self, client):
        html = client.get("/api-status").text
        assert "plataforma" in html.lower() or "Volver" in html
