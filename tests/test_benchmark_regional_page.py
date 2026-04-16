"""Tests for the farm regional benchmark page at /benchmark-regional (#235).

Router-disjoint FileResponse route; consumes existing
GET /api/farms/{farm_id}/regional-benchmark.
"""

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


class TestBenchmarkRegionalPage:
    def test_page_returns_200(self, client):
        resp = client.get("/benchmark-regional")
        assert resp.status_code == 200

    def test_page_has_spanish_labels(self, client):
        resp = client.get("/benchmark-regional")
        html = resp.text
        assert "Finca" in html
        assert "Benchmark" in html or "Regional" in html

    def test_page_has_farm_selector(self, client):
        resp = client.get("/benchmark-regional")
        assert 'id="bench-farm-select"' in resp.text

    def test_page_has_own_vs_regional_bars(self, client):
        resp = client.get("/benchmark-regional")
        html = resp.text
        assert 'id="bench-own-bar"' in html
        assert 'id="bench-regional-bar"' in html

    def test_page_has_percentile_display(self, client):
        resp = client.get("/benchmark-regional")
        assert 'id="bench-percentile"' in resp.text

    def test_page_has_better_than_pct_badge(self, client):
        resp = client.get("/benchmark-regional")
        html = resp.text
        assert 'id="bench-better-pct"' in html

    def test_page_calls_regional_benchmark_endpoint(self, client):
        resp = client.get("/benchmark-regional.js")
        assert resp.status_code == 200
        assert "/regional-benchmark" in resp.text

    def test_page_single_farm_graceful(self, client):
        resp = client.get("/benchmark-regional.js")
        js = resp.text
        assert "sin datos" in js.lower() or "Sin datos" in js or "unica" in js.lower() or "no-data" in js.lower()

    def test_js_file_served(self, client):
        resp = client.get("/benchmark-regional.js")
        assert resp.status_code == 200
        assert "fetch" in resp.text

    def test_page_has_title(self, client):
        resp = client.get("/benchmark-regional")
        assert "Benchmark Regional" in resp.text or "benchmark" in resp.text.lower()
