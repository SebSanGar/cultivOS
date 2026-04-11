"""Tests for GET /api/farms/{farm_id}/alert-effectiveness."""

from datetime import datetime, timedelta

from cultivos.db.models import Alert, Farm, Field, HealthScore


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Efectividad"):
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
        message="Salud baja detectada",
        sent_at=sent_at,
    )
    db.add(alert)
    db.commit()
    return alert


def _make_health(db, field_id, score, at):
    h = HealthScore(
        field_id=field_id,
        score=score,
        sources=["ndvi"],
        breakdown={},
        scored_at=at,
    )
    db.add(h)
    db.commit()
    return h


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/alert-effectiveness")
    assert resp.status_code == 404


def test_response_keys_present(client, db):
    """Response contains all required top-level keys."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/alert-effectiveness")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "farm_id" in data
    assert "alerts_analyzed" in data
    assert "alerts_with_followup" in data
    assert "improvement_rate_pct" in data
    assert "avg_improvement_pts" in data


def test_no_alerts_returns_zeros(client, db):
    """Farm with no alerts → all counts and rates are 0."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/alert-effectiveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["alerts_analyzed"] == 0
    assert data["alerts_with_followup"] == 0
    assert data["improvement_rate_pct"] == 0.0
    assert data["avg_improvement_pts"] == 0.0


def test_alert_with_health_improvement(client, db):
    """Alert followed by improved health score → improvement_rate > 0."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    sent = datetime(2026, 2, 1)
    # before the alert: low health
    _make_health(db, field.id, score=40.0, at=sent - timedelta(days=5))
    # alert sent
    _make_alert(db, farm.id, field.id, sent_at=sent)
    # after the alert (within 30 days): higher health
    _make_health(db, field.id, score=70.0, at=sent + timedelta(days=10))

    resp = client.get(f"/api/farms/{farm.id}/alert-effectiveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alerts_analyzed"] == 1
    assert data["alerts_with_followup"] == 1
    assert data["improvement_rate_pct"] > 0
    assert data["avg_improvement_pts"] > 0


def test_alert_with_no_followup_health_not_counted(client, db):
    """Alert with no HealthScore in 30 days after → alerts_with_followup = 0."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    sent = datetime(2026, 2, 1)
    _make_alert(db, farm.id, field.id, sent_at=sent)
    # health score only BEFORE, none after
    _make_health(db, field.id, score=50.0, at=sent - timedelta(days=3))

    resp = client.get(f"/api/farms/{farm.id}/alert-effectiveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alerts_analyzed"] == 1
    assert data["alerts_with_followup"] == 0
    assert data["improvement_rate_pct"] == 0.0


def test_health_score_outside_30_days_not_counted(client, db):
    """HealthScore more than 30 days after alert → does not count as followup."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    sent = datetime(2026, 2, 1)
    _make_alert(db, farm.id, field.id, sent_at=sent)
    _make_health(db, field.id, score=80.0, at=sent + timedelta(days=31))

    resp = client.get(f"/api/farms/{farm.id}/alert-effectiveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alerts_with_followup"] == 0


def test_improvement_rate_math(client, db):
    """2 alerts: 1 improved, 1 declined → improvement_rate_pct = 50.0."""
    farm = _make_farm(db)
    field1 = _make_field(db, farm.id, name="Campo Uno")
    field2 = _make_field(db, farm.id, name="Campo Dos")
    sent = datetime(2026, 3, 1)

    # Alert 1: health improves from 40 → 75
    _make_health(db, field1.id, score=40.0, at=sent - timedelta(days=2))
    _make_alert(db, farm.id, field1.id, sent_at=sent)
    _make_health(db, field1.id, score=75.0, at=sent + timedelta(days=7))

    # Alert 2: health declines from 70 → 45
    _make_health(db, field2.id, score=70.0, at=sent - timedelta(days=2))
    _make_alert(db, farm.id, field2.id, sent_at=sent)
    _make_health(db, field2.id, score=45.0, at=sent + timedelta(days=7))

    resp = client.get(f"/api/farms/{farm.id}/alert-effectiveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alerts_analyzed"] == 2
    assert data["alerts_with_followup"] == 2
    assert abs(data["improvement_rate_pct"] - 50.0) < 1.0


def test_avg_improvement_pts_math(client, db):
    """avg_improvement_pts = mean of (after - before) across alerts with followup."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Two alerts on same field at different times
    sent1 = datetime(2026, 1, 10)
    sent2 = datetime(2026, 2, 10)

    # Alert 1: +20 pts improvement (40 → 60)
    _make_health(db, field.id, score=40.0, at=sent1 - timedelta(days=2))
    _make_alert(db, farm.id, field.id, sent_at=sent1)
    _make_health(db, field.id, score=60.0, at=sent1 + timedelta(days=5))

    # Alert 2: +30 pts improvement (50 → 80)
    _make_health(db, field.id, score=50.0, at=sent2 - timedelta(days=2))
    _make_alert(db, farm.id, field.id, sent_at=sent2)
    _make_health(db, field.id, score=80.0, at=sent2 + timedelta(days=5))

    resp = client.get(f"/api/farms/{farm.id}/alert-effectiveness")
    assert resp.status_code == 200
    data = resp.json()
    # avg = (20 + 30) / 2 = 25
    assert abs(data["avg_improvement_pts"] - 25.0) < 1.0


def test_farm_id_in_response(client, db):
    """Response farm_id matches the requested farm."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/alert-effectiveness")
    assert resp.status_code == 200
    assert resp.json()["farm_id"] == farm.id
