"""Tests for GET /api/cooperatives/{coop_id}/field-leaderboard."""
import pytest
from cultivos.db.models import Cooperative, Farm, Field, HealthScore
from datetime import datetime


def _make_coop(db, name="Coop Test"):
    c = Cooperative(name=name)
    db.add(c)
    db.flush()
    return c


def _make_farm(db, coop_id, name="Finca Test"):
    f = Farm(name=name, cooperative_id=coop_id)
    db.add(f)
    db.flush()
    return f


def _make_field(db, farm_id, name="Parcela", crop_type="maiz", hectares=5.0):
    f = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=hectares)
    db.add(f)
    db.flush()
    return f


def _add_health(db, field_id, score, days_ago=0):
    from datetime import timedelta
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(hs)
    db.flush()
    return hs


def test_404_unknown_coop(client, db):
    r = client.get("/api/cooperatives/9999/field-leaderboard")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    coop = _make_coop(db)
    r = client.get(f"/api/cooperatives/{coop.id}/field-leaderboard")
    assert r.status_code == 200
    data = r.json()
    assert "cooperative_id" in data
    assert "total_fields" in data
    assert "fields" in data


def test_empty_coop_returns_empty_list(client, db):
    coop = _make_coop(db)
    r = client.get(f"/api/cooperatives/{coop.id}/field-leaderboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_fields"] == 0
    assert data["fields"] == []


def test_ranked_by_health_desc(client, db):
    """3 farms × 2 fields each → 6 fields ranked by latest health DESC."""
    coop = _make_coop(db)
    scores = [90.0, 70.0, 85.0, 60.0, 95.0, 40.0]
    for i, score in enumerate(scores):
        farm = _make_farm(db, coop.id, name=f"Finca {i}")
        field = _make_field(db, farm.id, name=f"Parcela {i}")
        _add_health(db, field.id, score)

    r = client.get(f"/api/cooperatives/{coop.id}/field-leaderboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_fields"] == 6
    healths = [f["latest_health"] for f in data["fields"] if f["latest_health"] is not None]
    assert healths == sorted(healths, reverse=True)


def test_rank_values_sequential(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    for i in range(3):
        field = _make_field(db, farm.id, name=f"P{i}")
        _add_health(db, field.id, 80.0 - i * 10)

    r = client.get(f"/api/cooperatives/{coop.id}/field-leaderboard")
    data = r.json()
    ranks = [f["rank"] for f in data["fields"]]
    assert ranks == list(range(1, len(ranks) + 1))


def test_field_with_no_health_score_appears_last(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field_with = _make_field(db, farm.id, name="Con salud")
    field_without = _make_field(db, farm.id, name="Sin salud")
    _add_health(db, field_with.id, 75.0)

    r = client.get(f"/api/cooperatives/{coop.id}/field-leaderboard")
    data = r.json()
    assert data["total_fields"] == 2
    # field with score comes first
    assert data["fields"][0]["latest_health"] == pytest.approx(75.0, abs=0.1)
    # field without score comes last with null
    assert data["fields"][-1]["latest_health"] is None


def test_latest_health_uses_most_recent_score(client, db):
    """When a field has multiple health scores, use the most recent."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 50.0, days_ago=10)
    _add_health(db, field.id, 80.0, days_ago=1)  # most recent

    r = client.get(f"/api/cooperatives/{coop.id}/field-leaderboard")
    data = r.json()
    assert data["fields"][0]["latest_health"] == pytest.approx(80.0, abs=0.1)


def test_field_item_schema_keys(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id)
    _add_health(db, field.id, 70.0)

    r = client.get(f"/api/cooperatives/{coop.id}/field-leaderboard")
    data = r.json()
    item = data["fields"][0]
    assert "rank" in item
    assert "farm_name" in item
    assert "field_id" in item
    assert "crop_type" in item
    assert "latest_health" in item
    assert "hectares" in item
