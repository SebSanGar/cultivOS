"""Tests for GET /api/cooperatives/{cooperative_id}/member-ranking endpoint."""

import pytest
from datetime import datetime
from cultivos.db.models import (
    Alert,
    Cooperative,
    Farm,
    Field,
    HealthScore,
    TreatmentRecord,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_coop(db, name="Cooperativa Test"):
    coop = Cooperative(name=name, state="Jalisco")
    db.add(coop)
    db.commit()
    return coop


def _make_farm(db, coop_id, name="Rancho Test"):
    farm = Farm(name=name, state="Jalisco", cooperative_id=coop_id, total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test"):
    field = Field(farm_id=farm_id, name=name, crop_type="maiz", hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_health(db, field_id, score, scored_at=None):
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=scored_at or datetime.utcnow(),
    )
    db.add(hs)
    db.commit()
    return hs


def _add_treatment(db, field_id, organic=True):
    tr = TreatmentRecord(
        field_id=field_id,
        health_score_used=60.0,
        problema="test",
        causa_probable="test",
        tratamiento="compost",
        costo_estimado_mxn=0,
        urgencia="baja",
        prevencion="ninguna",
        organic=organic,
    )
    db.add(tr)
    db.commit()
    return tr


def _add_alert(db, farm_id, field_id, status="sent", sent_at=None):
    alert = Alert(
        farm_id=farm_id,
        field_id=field_id,
        alert_type="low_health",
        message="test alert",
        status=status,
        sent_at=sent_at or datetime.utcnow(),
    )
    db.add(alert)
    db.commit()
    return alert


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_cooperative(client):
    r = client.get("/api/cooperatives/9999/member-ranking")
    assert r.status_code == 404


def test_three_farms_ranked_by_composite(client, db):
    """Three farms with different health scores are ranked correctly."""
    coop = _make_coop(db)

    farm_a = _make_farm(db, coop.id, "Rancho A")
    farm_b = _make_farm(db, coop.id, "Rancho B")
    farm_c = _make_farm(db, coop.id, "Rancho C")

    field_a = _make_field(db, farm_a.id, "Campo A")
    field_b = _make_field(db, farm_b.id, "Campo B")
    field_c = _make_field(db, farm_c.id, "Campo C")

    # High health farm A, low for C
    _add_health(db, field_a.id, 90.0)
    _add_health(db, field_b.id, 60.0)
    _add_health(db, field_c.id, 30.0)

    r = client.get(f"/api/cooperatives/{coop.id}/member-ranking")
    assert r.status_code == 200
    data = r.json()
    assert data["cooperative_id"] == coop.id
    members = data["members"]
    assert len(members) == 3

    # Ranked descending by composite_score
    scores = [m["composite_score"] for m in members]
    assert scores == sorted(scores, reverse=True)

    # Rank values are 1, 2, 3
    ranks = [m["rank"] for m in members]
    assert sorted(ranks) == [1, 2, 3]

    # Farm A has rank 1 (highest health → highest composite without regen/alert data)
    assert members[0]["farm_name"] == "Rancho A"
    assert members[0]["rank"] == 1


def test_missing_health_data_graceful(client, db):
    """Farm with no health scores gets health_avg=0.0, not an error."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    _make_field(db, farm.id)  # field with no health scores

    r = client.get(f"/api/cooperatives/{coop.id}/member-ranking")
    assert r.status_code == 200
    members = r.json()["members"]
    assert len(members) == 1
    assert members[0]["health_avg"] == 0.0


def test_no_alerts_graceful(client, db):
    """Farm with no alerts gets alert_response_rate=0.0, not an error."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 70.0)

    r = client.get(f"/api/cooperatives/{coop.id}/member-ranking")
    assert r.status_code == 200
    members = r.json()["members"]
    assert len(members) == 1
    assert members[0]["alert_response_rate"] == 0.0


def test_composite_formula(client, db):
    """composite_score = health*0.4 + regen*0.3 + alert_resp*0.3."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 80.0)
    # No treatments → organic_pct=0, health=80 → regen_score = 0*0.6 + 80*0.4 = 32.0
    # No alerts → alert_response_rate=0
    # composite = 80*0.4 + 32*0.3 + 0*0.3 = 32.0 + 9.6 = 41.6

    r = client.get(f"/api/cooperatives/{coop.id}/member-ranking")
    assert r.status_code == 200
    members = r.json()["members"]
    assert len(members) == 1
    assert members[0]["health_avg"] == 80.0
    assert members[0]["regen_score"] == pytest.approx(32.0, abs=1.0)
    assert members[0]["alert_response_rate"] == 0.0
    composite = members[0]["composite_score"]
    expected = round(80.0 * 0.4 + 32.0 * 0.3 + 0.0 * 0.3, 1)
    assert composite == pytest.approx(expected, abs=0.5)


def test_empty_cooperative_returns_empty_members(client, db):
    """Cooperative with no member farms returns empty members list."""
    coop = _make_coop(db)

    r = client.get(f"/api/cooperatives/{coop.id}/member-ranking")
    assert r.status_code == 200
    data = r.json()
    assert data["cooperative_id"] == coop.id
    assert data["members"] == []


def test_response_schema_fields_present(client, db):
    """Response has all required schema fields."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 50.0)

    r = client.get(f"/api/cooperatives/{coop.id}/member-ranking")
    assert r.status_code == 200
    data = r.json()
    assert "cooperative_id" in data
    assert "members" in data
    member = data["members"][0]
    for key in ("farm_id", "farm_name", "composite_score", "rank", "health_avg", "regen_score", "alert_response_rate"):
        assert key in member, f"Missing key: {key}"
