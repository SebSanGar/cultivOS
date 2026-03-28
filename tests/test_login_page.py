"""Tests for login page + auth flow."""

import pytest


# ── Page rendering ──

def test_login_page_renders(client):
    """GET /login returns 200 with the login page."""
    resp = client.get("/login")
    assert resp.status_code == 200
    html = resp.text
    assert "cultivOS" in html
    assert "Iniciar Sesion" in html


def test_login_page_has_username_field(client):
    """Login page has a username input field."""
    resp = client.get("/login")
    html = resp.text
    assert 'id="login-username"' in html


def test_login_page_has_password_field(client):
    """Login page has a password input field."""
    resp = client.get("/login")
    html = resp.text
    assert 'id="login-password"' in html


def test_login_page_has_submit_button(client):
    """Login page has a submit button."""
    resp = client.get("/login")
    html = resp.text
    assert 'id="login-submit"' in html


def test_login_page_has_register_toggle(client):
    """Login page has a link/button to toggle to registration mode."""
    resp = client.get("/login")
    html = resp.text
    assert 'id="toggle-register"' in html


def test_login_page_has_register_fields(client):
    """Login page has role selector for registration."""
    resp = client.get("/login")
    html = resp.text
    assert 'id="register-role"' in html


def test_login_page_has_error_container(client):
    """Login page has an error message container."""
    resp = client.get("/login")
    html = resp.text
    assert 'id="login-error"' in html


def test_login_js_served(client):
    """login.js is served correctly."""
    resp = client.get("/login.js")
    assert resp.status_code == 200
    js = resp.text
    assert "login" in js.lower()


# ── Auth API integration (used by login.js) ──

def test_login_api_success(client, db):
    """Successful login returns a JWT token."""
    client.post("/api/auth/register", json={
        "username": "testuser", "password": "secret123", "role": "admin"
    })
    resp = client.post("/api/auth/login", json={
        "username": "testuser", "password": "secret123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_api_failure(client, db):
    """Failed login returns 401."""
    resp = client.post("/api/auth/login", json={
        "username": "nonexistent", "password": "wrong"
    })
    assert resp.status_code == 401


def test_register_api_success(client, db):
    """Register creates a new user and returns 201."""
    resp = client.post("/api/auth/register", json={
        "username": "newfarmer", "password": "secret123", "role": "farmer"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newfarmer"
    assert data["role"] == "farmer"


def test_register_api_duplicate(client, db):
    """Duplicate registration returns 409."""
    client.post("/api/auth/register", json={
        "username": "dupuser", "password": "secret123", "role": "farmer"
    })
    resp = client.post("/api/auth/register", json={
        "username": "dupuser", "password": "secret123", "role": "farmer"
    })
    assert resp.status_code == 409
