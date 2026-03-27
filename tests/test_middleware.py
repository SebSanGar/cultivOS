"""Tests for API response standardization — error envelope, pagination, request logging."""

import logging

from tests.conftest import *  # noqa: F401,F403 — shared fixtures


class TestErrorEnvelope:
    """All 4xx/5xx responses use {"error": {"code": "...", "message": "..."}} envelope."""

    def test_error_response_has_error_envelope(self, client, admin_headers):
        """Any 4xx returns structured error envelope."""
        # 404 from a known route (farm not found)
        resp = client.get("/api/farms/9999")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
        assert body["error"]["code"] == "not_found"
        assert "not found" in body["error"]["message"].lower()

    def test_404_returns_json_not_html(self, client):
        """Unknown route returns JSON error, not HTML 404."""
        resp = client.get("/api/this-route-does-not-exist")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "not_found"
        assert resp.headers["content-type"].startswith("application/json")

    def test_500_returns_generic_message(self, app, db):
        """Internal error returns generic message without stack trace."""
        from fastapi import APIRouter
        from fastapi.testclient import TestClient
        from cultivos.db.session import get_db

        err_router = APIRouter()

        @err_router.get("/api/_test_500")
        def blow_up():
            raise RuntimeError("secret internal details")

        # Add route before StaticFiles mount by inserting into routes list
        app.include_router(err_router)
        # Move the new route before the StaticFiles catch-all
        app.routes.insert(0, app.routes.pop())

        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/_test_500")

        assert resp.status_code == 500
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "internal_error"
        assert "secret internal details" not in body["error"]["message"]
        assert "error interno" in body["error"]["message"].lower()
        app.dependency_overrides.clear()


class TestPagination:
    """List endpoints return paginated responses with data + meta."""

    def test_list_endpoint_has_pagination(self, client, admin_headers):
        """GET /api/farms returns {"data": [...], "meta": {"total": N, "page": N, "page_size": N}}."""
        # Create 3 farms
        for i in range(3):
            client.post("/api/farms", json={
                "name": f"Finca {i}", "location": "Jalisco",
                "latitude": 20.5 + i * 0.01, "longitude": -103.3,
                "size_hectares": 10.0,
            }, headers=admin_headers)

        resp = client.get("/api/farms")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 3
        assert body["meta"]["total"] == 3
        assert body["meta"]["page"] == 1
        assert "page_size" in body["meta"]

    def test_pagination_page_param(self, client, admin_headers):
        """Pagination respects page and page_size query params."""
        # Create 5 farms
        for i in range(5):
            client.post("/api/farms", json={
                "name": f"Finca {i}", "location": "Jalisco",
                "latitude": 20.5 + i * 0.01, "longitude": -103.3,
                "size_hectares": 10.0,
            }, headers=admin_headers)

        resp = client.get("/api/farms?page=1&page_size=2")
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["meta"]["total"] == 5
        assert body["meta"]["page"] == 1
        assert body["meta"]["page_size"] == 2

        # Page 3 should have 1 item
        resp2 = client.get("/api/farms?page=3&page_size=2")
        body2 = resp2.json()
        assert len(body2["data"]) == 1
        assert body2["meta"]["page"] == 3


class TestRequestLogging:
    """Request logging captures method, path, and duration."""

    def test_request_logging_captures_method_path(self, client, caplog):
        """Every request is logged with method, path, duration."""
        with caplog.at_level(logging.INFO, logger="cultivos.access"):
            client.get("/api/health")

        log_messages = [r.message for r in caplog.records if "cultivos.access" in r.name]
        assert len(log_messages) >= 1
        msg = log_messages[0]
        assert "GET" in msg
        assert "/api/health" in msg
        assert "ms" in msg.lower() or "ms)" in msg
