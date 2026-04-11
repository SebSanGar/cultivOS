"""Tests for GET /api/farms/{farm_id}/regional-benchmark

Compares a farm's average HealthScore against all farms in the same state.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore


# ── Helpers ────────────────────────────────────────────────────────────────────

def _farm(db, name="Finca Test", state="Jalisco"):
    f = Farm(name=name, municipality="Guadalajara", total_hectares=10.0, state=state)
    db.add(f)
    db.commit()
    return f


def _field(db, farm_id):
    f = Field(farm_id=farm_id, name="Lote A", crop_type="maiz", hectares=5.0)
    db.add(f)
    db.commit()
    return f


def _health(db, field_id, score, days_ago=1):
    db.add(HealthScore(
        field_id=field_id,
        score=score,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.commit()


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/regional-benchmark")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response has all required top-level keys."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/regional-benchmark")
    assert r.status_code == 200
    data = r.json()
    for key in ("farm_id", "farm_name", "state", "own_avg_health",
                "state_avg_health", "percentile_rank", "better_than_pct",
                "peer_farm_count"):
        assert key in data


def test_farm_with_no_health_scores(client, db):
    """Farm with no HealthScore records → own_avg_health is None."""
    farm = _farm(db)
    r = client.get(f"/api/farms/{farm.id}/regional-benchmark")
    assert r.status_code == 200
    assert r.json()["own_avg_health"] is None


def test_single_farm_in_state(client, db):
    """Only one farm in state → peer_farm_count=0, better_than_pct=100."""
    farm = _farm(db, state="Oaxaca")
    field = _field(db, farm.id)
    _health(db, field.id, score=80.0)

    r = client.get(f"/api/farms/{farm.id}/regional-benchmark")
    assert r.status_code == 200
    data = r.json()
    assert data["peer_farm_count"] == 0
    assert data["better_than_pct"] == 100.0


def test_farm_above_state_average(client, db):
    """Farm with high scores → better_than_pct > 50."""
    # Farm under test: avg health 90
    farm_high = _farm(db, name="Alto", state="Jalisco")
    field_high = _field(db, farm_high.id)
    _health(db, field_high.id, score=90.0)

    # Two peer farms with lower scores
    for score in [50.0, 60.0]:
        peer = _farm(db, name=f"Peer {score}", state="Jalisco")
        field = _field(db, peer.id)
        _health(db, field.id, score=score)

    r = client.get(f"/api/farms/{farm_high.id}/regional-benchmark")
    assert r.status_code == 200
    data = r.json()
    assert data["better_than_pct"] > 50.0
    assert data["peer_farm_count"] == 2


def test_farm_below_state_average(client, db):
    """Farm with low scores → better_than_pct < 50."""
    farm_low = _farm(db, name="Bajo", state="Jalisco")
    field_low = _field(db, farm_low.id)
    _health(db, field_low.id, score=30.0)

    for score in [70.0, 80.0]:
        peer = _farm(db, name=f"Peer {score}", state="Jalisco")
        field = _field(db, peer.id)
        _health(db, field.id, score=score)

    r = client.get(f"/api/farms/{farm_low.id}/regional-benchmark")
    assert r.status_code == 200
    data = r.json()
    assert data["better_than_pct"] < 50.0


def test_own_avg_health_correct(client, db):
    """own_avg_health is the mean of all HealthScore.score across all farm fields."""
    farm = _farm(db)
    field1 = _field(db, farm.id)
    field2 = _field(db, farm.id)
    _health(db, field1.id, score=70.0)
    _health(db, field2.id, score=90.0)

    r = client.get(f"/api/farms/{farm.id}/regional-benchmark")
    assert r.status_code == 200
    # avg of 70 and 90 = 80
    assert abs(r.json()["own_avg_health"] - 80.0) < 1.0


def test_state_avg_excludes_own_farm(client, db):
    """state_avg_health is computed from peer farms, not including own farm."""
    farm = _farm(db, name="FocusFarm", state="Jalisco")
    field = _field(db, farm.id)
    _health(db, field.id, score=50.0)

    peer = _farm(db, name="Peer", state="Jalisco")
    peer_field = _field(db, peer.id)
    _health(db, peer_field.id, score=80.0)

    r = client.get(f"/api/farms/{farm.id}/regional-benchmark")
    data = r.json()
    # state_avg should be 80 (peer only), not 65 (avg of both)
    assert abs(data["state_avg_health"] - 80.0) < 1.0


def test_farms_in_different_states_not_compared(client, db):
    """Farm in Oaxaca is not counted as peer for Jalisco farm."""
    farm = _farm(db, name="JaliscoFarm", state="Jalisco")
    field = _field(db, farm.id)
    _health(db, field.id, score=70.0)

    other = _farm(db, name="OaxacaFarm", state="Oaxaca")
    other_field = _field(db, other.id)
    _health(db, other_field.id, score=20.0)

    r = client.get(f"/api/farms/{farm.id}/regional-benchmark")
    assert r.status_code == 200
    data = r.json()
    assert data["peer_farm_count"] == 0


def test_percentile_rank_range(client, db):
    """percentile_rank is between 0 and 100 inclusive."""
    farm = _farm(db)
    field = _field(db, farm.id)
    _health(db, field.id, score=75.0)

    for score in [60.0, 80.0]:
        peer = _farm(db, name=f"P{score}")
        f = _field(db, peer.id)
        _health(db, f.id, score=score)

    r = client.get(f"/api/farms/{farm.id}/regional-benchmark")
    data = r.json()
    assert 0.0 <= data["percentile_rank"] <= 100.0
