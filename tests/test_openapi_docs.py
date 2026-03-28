"""Tests for OpenAPI documentation completeness."""

import pytest


@pytest.fixture
def openapi(client):
    """Fetch the OpenAPI schema."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    return resp.json()


def test_docs_endpoint_returns_200(client):
    """GET /docs should return the Swagger UI page."""
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_redoc_endpoint_returns_200(client):
    """GET /redoc should return the ReDoc page."""
    resp = client.get("/redoc")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_openapi_json_returns_200(client):
    """GET /openapi.json should return valid OpenAPI schema."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert "paths" in data
    assert "info" in data


def test_all_routes_have_summary(openapi):
    """Every API route should have a summary in the OpenAPI schema."""
    missing = []
    for path, methods in openapi["paths"].items():
        if not path.startswith("/api/"):
            continue
        for method, details in methods.items():
            if method in ("parameters",):
                continue
            if not details.get("summary"):
                missing.append(f"{method.upper()} {path}")
    assert missing == [], f"Routes missing summary: {missing}"


def test_all_routes_have_description(openapi):
    """Every API route should have a description in the OpenAPI schema."""
    missing = []
    for path, methods in openapi["paths"].items():
        if not path.startswith("/api/"):
            continue
        for method, details in methods.items():
            if method in ("parameters",):
                continue
            if not details.get("description"):
                missing.append(f"{method.upper()} {path}")
    assert missing == [], f"Routes missing description: {missing}"


def test_tag_descriptions_exist(openapi):
    """All tags used in the API should have descriptions."""
    tags_meta = {t["name"]: t for t in openapi.get("tags", [])}
    used_tags = set()
    for path, methods in openapi["paths"].items():
        if not path.startswith("/api/"):
            continue
        for method, details in methods.items():
            if method in ("parameters",):
                continue
            for tag in details.get("tags", []):
                used_tags.add(tag)
    missing = [t for t in used_tags if t not in tags_meta or not tags_meta[t].get("description")]
    assert missing == [], f"Tags missing descriptions: {missing}"


def test_openapi_info_has_contact(openapi):
    """OpenAPI info should include contact information."""
    info = openapi["info"]
    assert "contact" in info
    assert info["contact"].get("name")
