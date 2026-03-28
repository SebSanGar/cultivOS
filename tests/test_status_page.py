"""Tests for /estado — platform status dashboard page."""


class TestStatusPage:
    """Status dashboard page serves and contains expected elements."""

    def test_estado_route_returns_200(self, client):
        resp = client.get("/estado")
        assert resp.status_code == 200

    def test_estado_returns_html(self, client):
        resp = client.get("/estado")
        assert "text/html" in resp.headers.get("content-type", "")

    def test_page_contains_title(self, client):
        resp = client.get("/estado")
        assert "Estado de la Plataforma" in resp.text

    def test_page_contains_status_cards(self, client):
        resp = client.get("/estado")
        body = resp.text
        assert "status-api-version" in body
        assert "status-uptime" in body
        assert "status-farms" in body
        assert "status-fields" in body

    def test_page_contains_data_freshness(self, client):
        resp = client.get("/estado")
        body = resp.text
        assert "status-soil-ts" in body
        assert "status-ndvi-ts" in body
        assert "status-thermal-ts" in body
        assert "status-weather-ts" in body

    def test_page_loads_status_js(self, client):
        resp = client.get("/estado")
        assert "status.js" in resp.text

    def test_page_has_nav_with_links(self, client):
        resp = client.get("/estado")
        body = resp.text
        assert 'href="/"' in body
        assert 'href="/intel"' in body

    def test_status_js_accessible(self, client):
        resp = client.get("/status.js")
        assert resp.status_code == 200
