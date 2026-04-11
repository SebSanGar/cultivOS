"""Tests for date-range filter on GET /api/alerts/history."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Alert, AlertLog, Farm, Field
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


def _seed(db):
    farm = Farm(name="Rancho Fechas", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.commit()

    field = Field(farm_id=farm.id, name="Parcela Fecha", crop_type="maiz", hectares=10.0)
    db.add(field)
    db.commit()

    # Three alerts: old (30 days ago), mid (15 days ago), recent (today)
    old_ts = datetime(2026, 1, 1, 10, 0, 0)
    mid_ts = datetime(2026, 2, 15, 10, 0, 0)
    new_ts = datetime(2026, 4, 10, 10, 0, 0)

    db.add_all([
        Alert(
            farm_id=farm.id, field_id=field.id, alert_type="low_health",
            message="Alerta vieja", status="sent", created_at=old_ts,
        ),
        AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="irrigation",
            message="Log medio", severity="warning", created_at=mid_ts,
        ),
        Alert(
            farm_id=farm.id, field_id=field.id, alert_type="pest",
            message="Alerta reciente", status="pending", created_at=new_ts,
        ),
    ])
    db.commit()
    return farm.id


# --- date-range filter tests ---

def test_start_date_excludes_older_alerts(client, db):
    """start_date=2026-02-01 should exclude the Jan 1 alert."""
    _seed(db)
    resp = client.get("/api/alerts/history?start_date=2026-02-01")
    assert resp.status_code == 200
    data = resp.json()
    assert all(r["created_at"] >= "2026-02-01" for r in data)
    messages = [r["message"] for r in data]
    assert "Alerta vieja" not in messages
    assert "Log medio" in messages
    assert "Alerta reciente" in messages


def test_end_date_excludes_newer_alerts(client, db):
    """end_date=2026-01-31 should return only the Jan 1 alert."""
    _seed(db)
    resp = client.get("/api/alerts/history?end_date=2026-01-31")
    assert resp.status_code == 200
    data = resp.json()
    messages = [r["message"] for r in data]
    assert "Alerta vieja" in messages
    assert "Log medio" not in messages
    assert "Alerta reciente" not in messages


def test_date_range_combined(client, db):
    """start_date + end_date together return only February alert."""
    _seed(db)
    resp = client.get("/api/alerts/history?start_date=2026-02-01&end_date=2026-02-28")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["message"] == "Log medio"


def test_empty_date_range_returns_empty(client, db):
    """A range with no alerts returns empty list."""
    _seed(db)
    resp = client.get("/api/alerts/history?start_date=2025-01-01&end_date=2025-12-31")
    assert resp.status_code == 200
    assert resp.json() == []


def test_invalid_start_date_returns_422(client, db):
    """Non-ISO start_date triggers validation error."""
    resp = client.get("/api/alerts/history?start_date=not-a-date")
    assert resp.status_code == 422


def test_invalid_end_date_returns_422(client, db):
    """Non-ISO end_date triggers validation error."""
    resp = client.get("/api/alerts/history?end_date=31-13-2026")
    assert resp.status_code == 422


def test_no_date_filter_returns_all(client, db):
    """Without date params the existing behavior is preserved (all alerts returned)."""
    _seed(db)
    resp = client.get("/api/alerts/history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3


def test_date_range_with_farm_id_filter(client, db):
    """Date range combines correctly with existing farm_id filter."""
    farm_id = _seed(db)
    resp = client.get(f"/api/alerts/history?farm_id={farm_id}&start_date=2026-04-01")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["message"] == "Alerta reciente"
