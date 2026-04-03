"""Tests for security headers middleware."""

import pytest
from fastapi.testclient import TestClient


class TestSecurityHeaders:
    """Verify security headers are present on all responses."""

    def test_x_content_type_options(self, client):
        resp = client.get("/api/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, client):
        resp = client.get("/api/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_strict_transport_security(self, client):
        resp = client.get("/api/health")
        hsts = resp.headers.get("Strict-Transport-Security")
        assert hsts is not None
        assert "max-age=" in hsts

    def test_x_xss_protection(self, client):
        resp = client.get("/api/health")
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy(self, client):
        resp = client.get("/api/health")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_content_security_policy(self, client):
        resp = client.get("/api/health")
        csp = resp.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src" in csp

    def test_headers_on_api_endpoints(self, client):
        """Security headers appear on regular API endpoints too."""
        resp = client.get("/api/status")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_headers_on_error_responses(self, client):
        """Security headers appear even on 404 responses."""
        resp = client.get("/api/nonexistent-endpoint-xyz")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
