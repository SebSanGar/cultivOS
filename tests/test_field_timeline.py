"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/timeline."""

from datetime import datetime

from cultivos.db.models import (
    Farm, Field, HealthScore, NDVIResult, TreatmentRecord, Alert,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _farm(db):
    f = Farm(name="Rancho Timeline", state="Jalisco")
    db.add(f); db.commit(); return f


def _field(db, farm_id):
    f = Field(farm_id=farm_id, name="Campo Uno", crop_type="maiz")
    db.add(f); db.commit(); return f


def _health(db, field_id, score, at):
    h = HealthScore(field_id=field_id, score=score, sources=["ndvi"], breakdown={}, scored_at=at)
    db.add(h); db.commit(); return h


def _ndvi(db, field_id, mean, at):
    n = NDVIResult(
        field_id=field_id, ndvi_mean=mean, ndvi_std=0.05,
        ndvi_min=0.3, ndvi_max=0.9, pixels_total=1000, stress_pct=5.0,
        zones=[{"zone": "A", "mean": mean}], analyzed_at=at,
    )
    db.add(n); db.commit(); return n


def _treatment(db, field_id, text, cost, at):
    t = TreatmentRecord(
        field_id=field_id, health_score_used=70.0,
        problema="Plaga", causa_probable="Humedad", tratamiento=text,
        costo_estimado_mxn=cost, urgencia="media", prevencion="Rotacion",
        organic=True, created_at=at,
    )
    db.add(t); db.commit(); return t


def _alert(db, farm_id, field_id, msg, at):
    a = Alert(farm_id=farm_id, field_id=field_id, alert_type="low_health", message=msg, sent_at=at)
    db.add(a); db.commit(); return a


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client):
    resp = client.get("/api/farms/99999/fields/1/timeline")
    assert resp.status_code == 404


def test_404_unknown_field(client, db):
    farm = _farm(db)
    resp = client.get(f"/api/farms/{farm.id}/fields/99999/timeline")
    assert resp.status_code == 404


def test_empty_field_returns_empty_events(client, db):
    farm = _farm(db)
    field = _field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_id"] == field.id
    assert data["events"] == []


def test_response_keys_present(client, db):
    farm = _farm(db)
    field = _field(db, farm.id)
    _health(db, field.id, score=70.0, at=datetime(2026, 1, 10))
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert "field_id" in data
    assert "events" in data
    event = data["events"][0]
    assert "event_type" in event
    assert "date" in event
    assert "summary_es" in event
    assert "value" in event


def test_health_score_event_type(client, db):
    farm = _farm(db)
    field = _field(db, farm.id)
    _health(db, field.id, score=75.0, at=datetime(2026, 2, 1))
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline")
    event = resp.json()["events"][0]
    assert event["event_type"] == "health_score"
    assert "75" in event["summary_es"]
    assert abs(event["value"] - 75.0) < 0.01


def test_ndvi_event_type(client, db):
    farm = _farm(db)
    field = _field(db, farm.id)
    _ndvi(db, field.id, mean=0.65, at=datetime(2026, 2, 5))
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline")
    event = resp.json()["events"][0]
    assert event["event_type"] == "ndvi"
    assert "0.65" in event["summary_es"]
    assert abs(event["value"] - 0.65) < 0.001


def test_treatment_event_type(client, db):
    farm = _farm(db)
    field = _field(db, farm.id)
    _treatment(db, field.id, text="Aplicar neem organico", cost=500, at=datetime(2026, 2, 10))
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline")
    event = resp.json()["events"][0]
    assert event["event_type"] == "treatment"
    assert "neem" in event["summary_es"].lower()
    assert event["value"] == 500


def test_alert_event_type(client, db):
    farm = _farm(db)
    field = _field(db, farm.id)
    _alert(db, farm.id, field.id, msg="Salud critica detectada", at=datetime(2026, 2, 15))
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline")
    event = resp.json()["events"][0]
    assert event["event_type"] == "alert"
    assert "critica" in event["summary_es"].lower()


def test_events_sorted_ascending(client, db):
    """All 4 event types present → sorted by date ASC."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _alert(db, farm.id, field.id, "Alerta", at=datetime(2026, 4, 1))
    _treatment(db, field.id, "Tratamiento", 300, at=datetime(2026, 3, 1))
    _ndvi(db, field.id, 0.5, at=datetime(2026, 2, 1))
    _health(db, field.id, 60.0, at=datetime(2026, 1, 1))

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline")
    events = resp.json()["events"]
    assert len(events) == 4
    types = [e["event_type"] for e in events]
    assert types == ["health_score", "ndvi", "treatment", "alert"]


def test_date_filter_start_date(client, db):
    """start_date excludes events before it."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _health(db, field.id, 50.0, at=datetime(2026, 1, 10))  # excluded
    _health(db, field.id, 70.0, at=datetime(2026, 3, 10))  # included

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline?start_date=2026-02-01")
    events = resp.json()["events"]
    assert len(events) == 1
    assert abs(events[0]["value"] - 70.0) < 0.01


def test_date_filter_end_date(client, db):
    """end_date excludes events after it."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _health(db, field.id, 50.0, at=datetime(2026, 1, 10))  # included
    _health(db, field.id, 70.0, at=datetime(2026, 3, 10))  # excluded

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/timeline?end_date=2026-02-01")
    events = resp.json()["events"]
    assert len(events) == 1
    assert abs(events[0]["value"] - 50.0) < 0.01
