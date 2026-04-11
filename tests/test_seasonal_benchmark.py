"""Tests for GET /api/farms/{farm_id}/seasonal-benchmark.

Season calendar (Jalisco):
  temporal  Jun-Oct  (months 6-10)
  secas     Nov-May  (months 11-12 of year Y, months 1-5 of year Y+1)

Running in April 2026 → current season = secas 2025-26 (start_year 2025)
                      → prior season   = temporal 2025   (Jun-Oct 2025)
"""

from datetime import datetime

from cultivos.db.models import Farm, Field, HealthScore


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Temporal"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo A"):
    field = Field(farm_id=farm_id, name=name, crop_type="maiz")
    db.add(field)
    db.commit()
    return field


def _make_health(db, field_id, score, scored_at):
    h = HealthScore(
        field_id=field_id,
        score=score,
        sources=["ndvi"],
        breakdown={},
        scored_at=scored_at,
    )
    db.add(h)
    db.commit()
    return h


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client):
    resp = client.get("/api/farms/99999/seasonal-benchmark")
    assert resp.status_code == 404


def test_response_top_level_keys(client, db):
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/seasonal-benchmark")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_season" in data
    assert "prior_season" in data
    assert "fields" in data
    assert "overall_trend" in data


def test_field_keys_present(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Current season: secas 2025-26 → use Feb 2026 (month 2, secas)
    _make_health(db, field.id, score=70.0, scored_at=datetime(2026, 2, 1))

    resp = client.get(f"/api/farms/{farm.id}/seasonal-benchmark")
    assert resp.status_code == 200
    fields = resp.json()["fields"]
    assert len(fields) == 1
    f = fields[0]
    assert "field_id" in f
    assert "field_name" in f
    assert "current_avg" in f
    assert "prior_avg" in f
    assert "delta" in f
    assert "improved" in f


def test_two_seasons_correct_delta(client, db):
    """Field with data in both seasons → delta = current_avg - prior_avg.

    current = secas 2025-26  → Jan 2026 and Mar 2026  (avg 80)
    prior   = temporal 2025  → Jul 2025 and Sep 2025  (avg 60)
    """
    farm = _make_farm(db)
    field = _make_field(db, farm.id, name="Delta Field")

    # Prior season: temporal 2025 (Jun-Oct 2025)
    _make_health(db, field.id, score=60.0, scored_at=datetime(2025, 7, 15))
    _make_health(db, field.id, score=60.0, scored_at=datetime(2025, 9, 10))

    # Current season: secas 2025-26 (Nov 2025 – May 2026)
    _make_health(db, field.id, score=80.0, scored_at=datetime(2026, 1, 20))
    _make_health(db, field.id, score=80.0, scored_at=datetime(2026, 3, 5))

    resp = client.get(f"/api/farms/{farm.id}/seasonal-benchmark")
    assert resp.status_code == 200
    fields = resp.json()["fields"]
    f = next(x for x in fields if x["field_id"] == field.id)

    assert abs(f["current_avg"] - 80.0) < 0.1
    assert abs(f["prior_avg"] - 60.0) < 0.1
    assert abs(f["delta"] - 20.0) < 0.1
    assert f["improved"] is True


def test_only_current_season_prior_avg_null(client, db):
    """Field with data only in current season → prior_avg = null."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, name="No Prior")

    # Only current season data: secas 2025-26
    _make_health(db, field.id, score=75.0, scored_at=datetime(2026, 4, 1))

    resp = client.get(f"/api/farms/{farm.id}/seasonal-benchmark")
    assert resp.status_code == 200
    fields = resp.json()["fields"]
    f = next(x for x in fields if x["field_id"] == field.id)

    assert f["prior_avg"] is None
    assert f["delta"] is None


def test_overall_trend_improving(client, db):
    """Avg positive delta → overall_trend = improving."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    # Prior temporal 2025 avg=50, current secas 2025-26 avg=80
    _make_health(db, field.id, score=50.0, scored_at=datetime(2025, 8, 1))
    _make_health(db, field.id, score=80.0, scored_at=datetime(2026, 2, 1))

    resp = client.get(f"/api/farms/{farm.id}/seasonal-benchmark")
    assert resp.json()["overall_trend"] == "improving"


def test_overall_trend_stable_no_prior(client, db):
    """No prior season data → overall_trend = stable."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, score=70.0, scored_at=datetime(2026, 4, 1))

    resp = client.get(f"/api/farms/{farm.id}/seasonal-benchmark")
    assert resp.json()["overall_trend"] == "stable"
