"""Tests for farm alert escalation backlog.

GET /api/farms/{farm_id}/alert-escalations?days=30 — lists alerts that have
been active >=3 days without a treatment response on the same field.
"""

from datetime import datetime, timedelta

import pytest


def _now():
    return datetime.utcnow()


@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Escalado", state="Jalisco", total_hectares=40.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def other_farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Vecino", state="Jalisco", total_hectares=20.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _field(db, farm, name="Parcela A", crop="maiz"):
    from cultivos.db.models import Field
    fld = Field(farm_id=farm.id, name=name, crop_type=crop, hectares=5.0)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def _alert(db, farm, field, alert_type, days_ago, message="Alerta"):
    from cultivos.db.models import Alert
    sent_at = _now() - timedelta(days=days_ago)
    a = Alert(
        farm_id=farm.id,
        field_id=field.id,
        alert_type=alert_type,
        message=message,
        status="sent",
        sent_at=sent_at,
        created_at=sent_at,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _treatment(db, field, days_after_sent, sent_at):
    from cultivos.db.models import TreatmentRecord
    applied_at = sent_at + timedelta(days=days_after_sent)
    t = TreatmentRecord(
        field_id=field.id,
        health_score_used=50.0,
        problema="plaga",
        causa_probable="hongo",
        tratamiento="compost + rotation",
        costo_estimado_mxn=100,
        urgencia="media",
        prevencion="rotacion",
        organic=True,
        applied_at=applied_at,
    )
    db.add(t)
    db.commit()
    return t


def test_alert_escalations_unknown_farm(client):
    resp = client.get("/api/farms/9999/alert-escalations")
    assert resp.status_code == 404


def test_alert_escalations_empty_farm(client, farm):
    resp = client.get(f"/api/farms/{farm.id}/alert-escalations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["days"] == 30
    assert data["total"] == 0
    assert data["escalations"] == []


def test_alert_escalations_recent_alert_excluded(client, db, farm):
    """Alert less than 3 days old is not escalated."""
    field = _field(db, farm)
    _alert(db, farm, field, "low_health", days_ago=1)
    resp = client.get(f"/api/farms/{farm.id}/alert-escalations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["escalations"] == []


def test_alert_escalations_treated_excluded(client, db, farm):
    """Alert with a treatment applied after sent_at is not escalated."""
    field = _field(db, farm)
    a = _alert(db, farm, field, "pest", days_ago=5)
    _treatment(db, field, days_after_sent=1, sent_at=a.sent_at)
    resp = client.get(f"/api/farms/{farm.id}/alert-escalations")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_alert_escalations_untreated_included(client, db, farm):
    """Alert >=3 days old with no treatment response is escalated, severity mapped."""
    field = _field(db, farm, name="Parcela Seca")
    a = _alert(db, farm, field, "low_health", days_ago=6, message="Salud baja")
    resp = client.get(f"/api/farms/{farm.id}/alert-escalations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    esc = data["escalations"][0]
    assert esc["alert_id"] == a.id
    assert esc["field_id"] == field.id
    assert esc["field_name"] == "Parcela Seca"
    assert esc["alert_type"] == "low_health"
    assert esc["days_pending"] >= 3
    assert esc["severity"] == "critical"
    assert isinstance(esc["recommended_action_es"], str)
    assert len(esc["recommended_action_es"]) > 0


def test_alert_escalations_severity_by_type(client, db, farm):
    """Severity mapping: pest→high, irrigation→medium, low_health→critical."""
    f1 = _field(db, farm, name="A")
    f2 = _field(db, farm, name="B")
    f3 = _field(db, farm, name="C")
    _alert(db, farm, f1, "low_health", days_ago=4)
    _alert(db, farm, f2, "pest", days_ago=4)
    _alert(db, farm, f3, "irrigation", days_ago=4)
    resp = client.get(f"/api/farms/{farm.id}/alert-escalations")
    data = resp.json()
    assert data["total"] == 3
    by_type = {e["alert_type"]: e["severity"] for e in data["escalations"]}
    assert by_type["low_health"] == "critical"
    assert by_type["pest"] == "high"
    assert by_type["irrigation"] == "medium"


def test_alert_escalations_sorted_days_pending_desc(client, db, farm):
    """Returned list is sorted by days_pending DESC."""
    field = _field(db, farm)
    _alert(db, farm, field, "low_health", days_ago=4)
    _alert(db, farm, field, "pest", days_ago=10)
    _alert(db, farm, field, "irrigation", days_ago=7)
    resp = client.get(f"/api/farms/{farm.id}/alert-escalations")
    data = resp.json()
    assert data["total"] == 3
    pending = [e["days_pending"] for e in data["escalations"]]
    assert pending == sorted(pending, reverse=True)
    assert pending[0] >= pending[-1]


def test_alert_escalations_days_window(client, db, farm):
    """Alerts beyond the requested `days` window are not counted."""
    field = _field(db, farm)
    _alert(db, farm, field, "pest", days_ago=5)     # within 30-day window
    _alert(db, farm, field, "pest", days_ago=45)    # beyond 30-day window
    resp = client.get(f"/api/farms/{farm.id}/alert-escalations?days=30")
    data = resp.json()
    assert data["days"] == 30
    assert data["total"] == 1

    # Wider window catches both
    resp2 = client.get(f"/api/farms/{farm.id}/alert-escalations?days=60")
    assert resp2.json()["total"] == 2


def test_alert_escalations_excludes_other_farm(client, db, farm, other_farm):
    own = _field(db, farm, name="Propia")
    foreign = _field(db, other_farm, name="Ajena")
    _alert(db, farm, own, "low_health", days_ago=5)
    _alert(db, other_farm, foreign, "pest", days_ago=5)
    resp = client.get(f"/api/farms/{farm.id}/alert-escalations")
    data = resp.json()
    assert data["total"] == 1
    assert data["escalations"][0]["field_id"] == own.id
