"""Tests for #182 — Farmer observation log.

POST /api/farms/{farm_id}/fields/{field_id}/observations
GET  /api/farms/{farm_id}/fields/{field_id}/observations
"""

import pytest


def _create_farm(client):
    r = client.post("/api/farms", json={"name": "Rancho Test", "owner_name": "Don Test"})
    assert r.status_code == 201
    return r.json()["id"]


def _create_field(client, farm_id):
    r = client.post(
        f"/api/farms/{farm_id}/fields",
        json={"name": "Parcela 1", "crop_type": "maiz", "hectares": 5.0},
    )
    assert r.status_code == 201
    return r.json()["id"]


# --- POST ---

def test_post_creates_observation(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    r = client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/observations",
        json={
            "observation_es": "Las hojas se están poniendo amarillas",
            "observation_type": "problem",
            "crop_stage": "vegetativo",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["observation_es"] == "Las hojas se están poniendo amarillas"
    assert data["observation_type"] == "problem"
    assert data["crop_stage"] == "vegetativo"
    assert data["field_id"] == field_id
    assert "id" in data
    assert "created_at" in data


def test_post_without_crop_stage(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    r = client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/observations",
        json={"observation_es": "La cosecha salió muy bien", "observation_type": "success"},
    )
    assert r.status_code == 201
    assert r.json()["crop_stage"] is None


def test_post_invalid_observation_type_returns_422(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    r = client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/observations",
        json={"observation_es": "algo", "observation_type": "invalid_type"},
    )
    assert r.status_code == 422


def test_post_unknown_farm_returns_404(client):
    r = client.post(
        "/api/farms/9999/fields/1/observations",
        json={"observation_es": "algo", "observation_type": "neutral"},
    )
    assert r.status_code == 404


def test_post_unknown_field_returns_404(client):
    farm_id = _create_farm(client)
    r = client.post(
        f"/api/farms/{farm_id}/fields/9999/observations",
        json={"observation_es": "algo", "observation_type": "neutral"},
    )
    assert r.status_code == 404


# --- GET ---

def test_get_returns_empty_list(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    r = client.get(f"/api/farms/{farm_id}/fields/{field_id}/observations")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["field_id"] == field_id


def test_get_lists_all_observations(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    for obs_type, text in [("problem", "Plaga detectada"), ("success", "Buena germinacion"), ("neutral", "Revisión rutinaria")]:
        client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/observations",
            json={"observation_es": text, "observation_type": obs_type},
        )
    r = client.get(f"/api/farms/{farm_id}/fields/{field_id}/observations")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_get_filter_by_type(client):
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/observations",
        json={"observation_es": "Plaga detectada", "observation_type": "problem"},
    )
    client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/observations",
        json={"observation_es": "Todo bien", "observation_type": "success"},
    )
    r = client.get(f"/api/farms/{farm_id}/fields/{field_id}/observations?type=problem")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["observation_type"] == "problem"


def test_get_unknown_field_returns_404(client):
    farm_id = _create_farm(client)
    r = client.get(f"/api/farms/{farm_id}/fields/9999/observations")
    assert r.status_code == 404


def test_get_returns_newest_first(client):
    """Observations should be returned newest first."""
    from datetime import datetime, timedelta
    farm_id = _create_farm(client)
    field_id = _create_field(client, farm_id)
    client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/observations",
        json={"observation_es": "Primera observacion", "observation_type": "neutral"},
    )
    client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/observations",
        json={"observation_es": "Segunda observacion", "observation_type": "neutral"},
    )
    r = client.get(f"/api/farms/{farm_id}/fields/{field_id}/observations")
    items = r.json()["items"]
    assert items[0]["observation_es"] == "Segunda observacion"
