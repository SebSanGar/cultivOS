"""M2 — Register form: drop admin trap + surface real API errors.

Tests:
  1. login.html has NO admin role option (only farmer + researcher)
  2. Error envelope from register/login endpoints uses {"error":{"message":...}}
  3. login.js reads error.message (not .detail) for register + login errors
"""

import re
from pathlib import Path

import pytest

from cultivos.db.models import User
from cultivos.auth import hash_password


FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


# ── HTML source tests ─────────────────────────────────────────────────

class TestLoginHtmlRoleOptions:
    """login.html role <select> must NOT include admin."""

    def test_no_admin_option_in_html(self):
        html = (FRONTEND / "login.html").read_text()
        assert 'value="admin"' not in html, "Admin option must be removed from role select"

    def test_exactly_two_role_options(self):
        html = (FRONTEND / "login.html").read_text()
        options = re.findall(r'<option\s+value="(\w+)"[^>]*>', html)
        role_values = [v for v in options if v in ("farmer", "researcher", "admin")]
        assert sorted(role_values) == ["farmer", "researcher"], (
            f"Expected exactly farmer + researcher, got {role_values}"
        )


# ── Error envelope tests (backend confirms structured format) ─────────

class TestRegisterErrorEnvelope:
    """POST /api/auth/register errors must use {"error":{"message":...}} envelope."""

    def test_duplicate_username_409_envelope(self, client, db):
        db.add(User(
            username="existing_user",
            hashed_password=hash_password("secret123"),
            role="farmer",
        ))
        db.commit()

        resp = client.post("/api/auth/register", json={
            "username": "existing_user",
            "password": "secret123",
            "role": "farmer",
        })
        assert resp.status_code == 409
        body = resp.json()
        assert "error" in body, f"Expected error envelope, got {body}"
        assert "message" in body["error"], f"Expected error.message, got {body}"
        assert "already taken" in body["error"]["message"].lower()

    def test_admin_register_403_envelope(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "sneaky_admin",
            "password": "secret123",
            "role": "admin",
        })
        assert resp.status_code == 403
        body = resp.json()
        assert "error" in body, f"Expected error envelope, got {body}"
        assert "message" in body["error"]
        assert "admin" in body["error"]["message"].lower()


class TestLoginErrorEnvelope:
    """POST /api/auth/login errors must use {"error":{"message":...}} envelope."""

    def test_invalid_credentials_401_envelope(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass",
        })
        assert resp.status_code == 401
        body = resp.json()
        assert "error" in body, f"Expected error envelope, got {body}"
        assert "message" in body["error"]


# ── JavaScript error reading tests ────────────────────────────────────

class TestLoginJsErrorReading:
    """login.js must read error.message, not .detail, from error responses."""

    def test_register_error_reads_error_message(self):
        js = (FRONTEND / "login.js").read_text()
        reg_block = js[js.find("regResp.ok"):]
        assert ".error" in reg_block and ".message" in reg_block, (
            "Register error handler must read .error.message from response"
        )

    def test_login_error_reads_error_message(self):
        js = (FRONTEND / "login.js").read_text()
        login_block = js[js.find("loginResp.ok"):]
        assert ".error" in login_block and ".message" in login_block, (
            "Login error handler must read .error.message from response"
        )
