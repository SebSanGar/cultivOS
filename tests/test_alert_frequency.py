"""Tests for GET /api/farms/{farm_id}/alert-frequency."""

from datetime import datetime, timedelta

from cultivos.db.models import Alert, Farm, Field


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Frecuencia"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Uno", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type)
    db.add(field)
    db.commit()
    return field


def _make_alert(db, farm_id, field_id, sent_at, alert_type="low_health"):
    alert = Alert(
        farm_id=farm_id,
        field_id=field_id,
        alert_type=alert_type,
        message="Alerta de prueba",
        sent_at=sent_at,
    )
    db.add(alert)
    db.commit()
    return alert


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/alert-frequency")
    assert resp.status_code == 404


def test_response_keys_present(client, db):
    """Response contains required top-level keys."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/alert-frequency")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "farm_id" in data
    assert "fields" in data
    assert "overall_alert_load" in data


def test_no_alerts_returns_zeros(client, db):
    """Farm with no alerts → monthly_avg=0, trend=stable for each field."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    resp = client.get(f"/api/farms/{farm.id}/alert-frequency")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["overall_alert_load"] == 0.0
    assert len(data["fields"]) == 1
    item = data["fields"][0]
    assert item["field_id"] == field.id
    assert item["monthly_avg"] == 0.0
    assert item["trend"] == "stable"


def test_monthly_avg_calculation(client, db):
    """3 alerts spread across 3 months → monthly_avg = 0.5 (3 alerts / 6 months)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    now = datetime(2026, 4, 1)

    # 3 alerts spread across months 1, 2, 3 ago
    for months_ago in [1, 2, 3]:
        _make_alert(
            db, farm.id, field.id,
            sent_at=now - timedelta(days=months_ago * 30),
        )

    resp = client.get(f"/api/farms/{farm.id}/alert-frequency")
    assert resp.status_code == 200
    data = resp.json()
    item = data["fields"][0]
    # 3 alerts over 6-month window → avg = 3/6 = 0.5
    assert abs(item["monthly_avg"] - 0.5) < 0.05


def test_dominant_type_most_frequent(client, db):
    """dominant_type = alert_type that appears most often in 6-month window."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    now = datetime(2026, 4, 1)

    # 3 irrigation alerts, 1 pest alert
    for i in range(3):
        _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=i * 20 + 5), alert_type="irrigation")
    _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=70), alert_type="pest")

    resp = client.get(f"/api/farms/{farm.id}/alert-frequency")
    assert resp.status_code == 200
    data = resp.json()
    item = data["fields"][0]
    assert item["dominant_type"] == "irrigation"


def test_trend_increasing(client, db):
    """trend=increasing when last 2 months have more alerts than prior 2 months."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    now = datetime(2026, 4, 1)

    # last 2 months: 4 alerts
    for i in range(4):
        _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=i * 7 + 1))
    # prior 2 months (months 3-4 ago): 1 alert
    _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=75))

    resp = client.get(f"/api/farms/{farm.id}/alert-frequency")
    assert resp.status_code == 200
    data = resp.json()
    item = data["fields"][0]
    assert item["trend"] == "increasing"


def test_trend_decreasing(client, db):
    """trend=decreasing when last 2 months have fewer alerts than prior 2 months."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    now = datetime(2026, 4, 1)

    # last 2 months: 1 alert
    _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=10))
    # prior 2 months (months 3-4 ago): 4 alerts
    for i in range(4):
        _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=70 + i * 10))

    resp = client.get(f"/api/farms/{farm.id}/alert-frequency")
    assert resp.status_code == 200
    data = resp.json()
    item = data["fields"][0]
    assert item["trend"] == "decreasing"


def test_trend_stable_equal_counts(client, db):
    """trend=stable when last 2 months = prior 2 months alert count."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    now = datetime(2026, 4, 1)

    # last 2 months: 2 alerts
    _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=10))
    _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=40))
    # prior 2 months: 2 alerts
    _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=70))
    _make_alert(db, farm.id, field.id, sent_at=now - timedelta(days=100))

    resp = client.get(f"/api/farms/{farm.id}/alert-frequency")
    assert resp.status_code == 200
    data = resp.json()
    item = data["fields"][0]
    assert item["trend"] == "stable"


def test_overall_alert_load(client, db):
    """overall_alert_load = avg of per-field monthly_avg across all fields."""
    farm = _make_farm(db)
    field1 = _make_field(db, farm.id, name="Campo Uno")
    field2 = _make_field(db, farm.id, name="Campo Dos")
    now = datetime(2026, 4, 1)

    # field1: 6 alerts in 6 months → avg = 1.0
    for i in range(6):
        _make_alert(db, farm.id, field1.id, sent_at=now - timedelta(days=i * 25 + 1))
    # field2: 0 alerts → avg = 0.0

    resp = client.get(f"/api/farms/{farm.id}/alert-frequency")
    assert resp.status_code == 200
    data = resp.json()
    # overall = (1.0 + 0.0) / 2 = 0.5
    assert abs(data["overall_alert_load"] - 0.5) < 0.1
