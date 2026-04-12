"""Tests for #190 — Farmer observation insights aggregate.

GET /api/farms/{farm_id}/observation-insights?days=30

Aggregates FarmerObservation rows across all fields in a farm into
count-by-type, top types, and period summary.
"""

from datetime import datetime, timedelta


def _create_farm(client, name="Rancho Insights"):
    r = client.post("/api/farms", json={"name": name, "owner_name": "Don Test"})
    assert r.status_code == 201
    return r.json()["id"]


def _create_field(client, farm_id, name="Parcela 1"):
    r = client.post(
        f"/api/farms/{farm_id}/fields",
        json={"name": name, "crop_type": "maiz", "hectares": 5.0},
    )
    assert r.status_code == 201
    return r.json()["id"]


def _post_obs(client, farm_id, field_id, obs_type, text="observacion"):
    r = client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/observations",
        json={"observation_es": text, "observation_type": obs_type},
    )
    assert r.status_code == 201
    return r.json()


def test_unknown_farm_returns_404(client):
    r = client.get("/api/farms/9999/observation-insights")
    assert r.status_code == 404


def test_empty_farm_returns_zeros(client):
    farm_id = _create_farm(client)
    r = client.get(f"/api/farms/{farm_id}/observation-insights")
    assert r.status_code == 200
    data = r.json()
    assert data["farm_id"] == farm_id
    assert data["total_observations"] == 0
    assert data["observations_by_type"] == []
    assert data["last_observed_at"] is None
    assert data["period_days"] == 30


def test_counts_by_type_with_pct(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    _post_obs(client, farm_id, field_id, "problem", "plaga")
    _post_obs(client, farm_id, field_id, "problem", "hongo")
    _post_obs(client, farm_id, field_id, "success", "cosecha buena")
    _post_obs(client, farm_id, field_id, "neutral", "revision")
    r = client.get(f"/api/farms/{farm_id}/observation-insights")
    assert r.status_code == 200
    data = r.json()
    assert data["total_observations"] == 4
    by_type = {row["type"]: row for row in data["observations_by_type"]}
    assert by_type["problem"]["count"] == 2
    assert by_type["problem"]["pct"] == 50.0
    assert by_type["success"]["count"] == 1
    assert by_type["success"]["pct"] == 25.0
    assert by_type["neutral"]["count"] == 1
    assert by_type["neutral"]["pct"] == 25.0


def test_sorted_by_count_desc(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    for _ in range(3):
        _post_obs(client, farm_id, field_id, "success", "ok")
    _post_obs(client, farm_id, field_id, "problem", "x")
    r = client.get(f"/api/farms/{farm_id}/observation-insights")
    data = r.json()
    assert data["observations_by_type"][0]["type"] == "success"
    assert data["observations_by_type"][0]["count"] == 3


def test_aggregates_across_multiple_fields(client):
    farm_id = _create_farm(client)
    field_a = _create_field(client, farm_id, "A")
    field_b = _create_field(client, farm_id, "B")
    _post_obs(client, farm_id, field_a, "problem", "a1")
    _post_obs(client, farm_id, field_b, "problem", "b1")
    _post_obs(client, farm_id, field_b, "success", "b2")
    r = client.get(f"/api/farms/{farm_id}/observation-insights")
    data = r.json()
    assert data["total_observations"] == 3
    by_type = {row["type"]: row["count"] for row in data["observations_by_type"]}
    assert by_type["problem"] == 2
    assert by_type["success"] == 1


def test_period_days_filter(client, db):
    from cultivos.db.models import FarmerObservation
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    old = FarmerObservation(
        field_id=field_id,
        observation_es="vieja",
        observation_type="neutral",
        created_at=datetime.utcnow() - timedelta(days=45),
    )
    recent = FarmerObservation(
        field_id=field_id,
        observation_es="nueva",
        observation_type="problem",
        created_at=datetime.utcnow() - timedelta(days=5),
    )
    db.add_all([old, recent])
    db.commit()

    r = client.get(f"/api/farms/{farm_id}/observation-insights?days=30")
    data = r.json()
    assert data["total_observations"] == 1
    assert data["observations_by_type"][0]["type"] == "problem"

    r = client.get(f"/api/farms/{farm_id}/observation-insights?days=60")
    data = r.json()
    assert data["total_observations"] == 2


def test_last_observed_at_returned(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    _post_obs(client, farm_id, field_id, "neutral", "hola")
    r = client.get(f"/api/farms/{farm_id}/observation-insights")
    data = r.json()
    assert data["last_observed_at"] is not None


def test_only_counts_own_farm_observations(client):
    farm_a = _create_farm(client, "A")
    farm_b = _create_farm(client, "B")
    field_a = _create_field(client, farm_a)
    field_b = _create_field(client, farm_b)
    _post_obs(client, farm_a, field_a, "problem", "a")
    _post_obs(client, farm_b, field_b, "success", "b")
    _post_obs(client, farm_b, field_b, "success", "b2")
    r = client.get(f"/api/farms/{farm_a}/observation-insights")
    assert r.json()["total_observations"] == 1
    r = client.get(f"/api/farms/{farm_b}/observation-insights")
    assert r.json()["total_observations"] == 2


def test_invalid_days_param_returns_422(client):
    farm_id = _create_farm(client)
    r = client.get(f"/api/farms/{farm_id}/observation-insights?days=0")
    assert r.status_code == 422
