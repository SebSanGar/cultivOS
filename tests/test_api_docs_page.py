"""Tests for the interactive API docs page at /docs-api."""

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


class TestApiDocsPageLoad:
    """Page loads and contains required HTML structure."""

    def test_page_returns_200(self, client):
        resp = client.get("/docs-api")
        assert resp.status_code == 200

    def test_page_has_title(self, client):
        resp = client.get("/docs-api")
        assert "Referencia API" in resp.text or "API" in resp.text

    def test_page_has_cultivOS_branding(self, client):
        resp = client.get("/docs-api")
        html = resp.text
        assert "cultivOS" in html

    def test_page_has_nav(self, client):
        resp = client.get("/docs-api")
        assert "<nav" in resp.text

    def test_page_has_styles_link(self, client):
        resp = client.get("/docs-api")
        assert "/styles.css" in resp.text


class TestApiDocsLinks:
    """Page contains links to /docs (Swagger) and /redoc."""

    def test_has_swagger_link(self, client):
        resp = client.get("/docs-api")
        assert "/docs" in resp.text

    def test_has_redoc_link(self, client):
        resp = client.get("/docs-api")
        assert "/redoc" in resp.text

    def test_has_openapi_json_link(self, client):
        resp = client.get("/docs-api")
        assert "/openapi.json" in resp.text


class TestApiDocsContent:
    """Page shows API categories and descriptions."""

    def test_has_api_categories_container(self, client):
        resp = client.get("/docs-api")
        assert 'id="api-categories"' in resp.text

    def test_has_api_docs_script(self, client):
        resp = client.get("/docs-api")
        assert "/api-docs.js" in resp.text

    def test_page_has_description_text(self, client):
        resp = client.get("/docs-api")
        html = resp.text
        assert "agricultura" in html.lower() or "precision" in html.lower() or "inteligencia" in html.lower()

    def test_page_has_stats_strip(self, client):
        resp = client.get("/docs-api")
        html = resp.text
        assert 'id="api-endpoint-count"' in html
        assert 'id="api-tag-count"' in html


class TestOpenApiEndpoint:
    """The /openapi.json endpoint works for the JS to consume."""

    def test_openapi_json_returns_200(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200

    def test_openapi_json_has_paths(self, client):
        data = client.get("/openapi.json").json()
        assert "paths" in data
        assert len(data["paths"]) > 0

    def test_openapi_json_has_tags(self, client):
        data = client.get("/openapi.json").json()
        assert "tags" in data
        assert len(data["tags"]) > 0
