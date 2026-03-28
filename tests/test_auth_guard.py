"""Tests for auth guard — unauthenticated redirect + nav user info."""

import pytest


# ── Auth guard script presence on protected pages ──

def test_index_has_auth_guard(client):
    """Dashboard page includes auth-guard.js."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "auth-guard.js" in resp.text


def test_field_page_has_auth_guard(client):
    """Field detail page includes auth-guard.js."""
    resp = client.get("/campo")
    assert resp.status_code == 200
    assert "auth-guard.js" in resp.text


def test_intel_has_auth_guard(client):
    """Intel dashboard includes auth-guard.js."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert "auth-guard.js" in resp.text


def test_knowledge_has_auth_guard(client):
    """Knowledge page includes auth-guard.js."""
    resp = client.get("/conocimiento")
    assert resp.status_code == 200
    assert "auth-guard.js" in resp.text


# ── Login page does NOT have auth guard (would cause redirect loop) ──

def test_login_page_no_auth_guard(client):
    """Login page does NOT include auth-guard.js (would cause redirect loop)."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "auth-guard.js" not in resp.text


# ── Walkthrough exempt from auth guard ──

def test_walkthrough_no_auth_guard(client):
    """Walkthrough page does NOT include auth-guard.js (public demo)."""
    resp = client.get("/recorrido")
    assert resp.status_code == 200
    assert "auth-guard.js" not in resp.text


# ── auth-guard.js is served correctly ──

def test_auth_guard_js_served(client):
    """auth-guard.js is served as a static file."""
    resp = client.get("/auth-guard.js")
    assert resp.status_code == 200
    js = resp.text
    assert "cultivOS_token" in js
    assert "/login" in js


# ── Nav bar has user info section ──

def test_index_nav_has_user_section(client):
    """Dashboard nav has a user-info section for username + logout."""
    resp = client.get("/")
    html = resp.text
    assert 'id="nav-user-info"' in html


def test_field_nav_has_user_section(client):
    """Field page nav has a user-info section."""
    resp = client.get("/campo")
    html = resp.text
    assert 'id="nav-user-info"' in html


def test_intel_nav_has_user_section(client):
    """Intel page nav has a user-info section."""
    resp = client.get("/intel")
    html = resp.text
    assert 'id="nav-user-info"' in html


def test_knowledge_nav_has_user_section(client):
    """Knowledge page nav has a user-info section."""
    resp = client.get("/conocimiento")
    html = resp.text
    assert 'id="nav-user-info"' in html


# ── Auth guard JS content checks ──

def test_auth_guard_redirects_without_token(client):
    """auth-guard.js checks for cultivOS_token and redirects to /login."""
    resp = client.get("/auth-guard.js")
    js = resp.text
    assert "localStorage" in js
    assert "cultivOS_token" in js
    assert "window.location" in js or "location.href" in js


def test_auth_guard_has_logout_function(client):
    """auth-guard.js includes a logout function."""
    resp = client.get("/auth-guard.js")
    js = resp.text
    assert "logout" in js.lower()
    assert "removeItem" in js


def test_auth_guard_shows_username(client):
    """auth-guard.js populates username from localStorage."""
    resp = client.get("/auth-guard.js")
    js = resp.text
    assert "cultivOS_user" in js
