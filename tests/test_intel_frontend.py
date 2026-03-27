"""Tests for the intelligence dashboard frontend (/intel)."""

import pytest


@pytest.fixture
def researcher_headers(client):
    """Register a researcher user and return auth headers."""
    client.post("/api/auth/register", json={
        "username": "testresearcher", "password": "secret123", "role": "researcher"
    })
    resp = client.post("/api/auth/login", json={
        "username": "testresearcher", "password": "secret123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_intel_page_loads(client):
    """GET /intel returns 200 with 'Panel de Inteligencia'."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert "Panel de Inteligencia" in resp.text


def test_intel_shows_farm_map_placeholder(client):
    """HTML has map container div."""
    resp = client.get("/intel")
    html = resp.text
    assert 'id="intel-map"' in html


def test_intel_shows_anomaly_alerts(client):
    """HTML has anomaly cards container that JS fills from /api/intel/anomalies."""
    resp = client.get("/intel")
    html = resp.text
    assert 'id="intel-anomalies"' in html


def test_intel_shows_soil_trend_chart(client):
    """HTML has chart container for soil trends."""
    resp = client.get("/intel")
    html = resp.text
    assert 'id="intel-soil-chart"' in html


def test_intel_researcher_view_hides_actions(client):
    """HTML has admin-only elements marked with class for JS to hide for researchers."""
    resp = client.get("/intel")
    html = resp.text
    # Admin action buttons should have a class that JS uses to show/hide based on role
    assert "admin-only" in html
