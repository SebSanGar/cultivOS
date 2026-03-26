"""Tests for Soil Analysis CRUD endpoints."""

import pytest


@pytest.fixture
def farm_and_field(client, admin_headers):
    """Create a farm + field and return (farm_id, field_id)."""
    farm = client.post("/api/farms", json={"name": "Rancho Tierra"}, headers=admin_headers)
    farm_id = farm.json()["id"]
    field = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Suelo", "crop_type": "maiz", "hectares": 10,
    })
    field_id = field.json()["id"]
    return farm_id, field_id


SAMPLE_SOIL = {
    "ph": 6.5,
    "organic_matter_pct": 3.2,
    "nitrogen_ppm": 45.0,
    "phosphorus_ppm": 22.0,
    "potassium_ppm": 180.0,
    "texture": "loam",
    "moisture_pct": 28.5,
    "electrical_conductivity": 1.2,
    "depth_cm": 30.0,
    "notes": "Sample taken after rain",
    "sampled_at": "2026-03-20T10:00:00",
}


# ── Create ────────────────────────────────────────────────────────────

class TestCreateSoilAnalysis:
    def test_create_full(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json=SAMPLE_SOIL,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["ph"] == 6.5
        assert data["texture"] == "loam"
        assert data["field_id"] == field_id
        assert data["id"] is not None

    def test_create_minimal(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json={"sampled_at": "2026-03-20T10:00:00"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["ph"] is None
        assert data["sampled_at"] is not None

    def test_create_missing_sampled_at(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json={"ph": 7.0},
        )
        assert resp.status_code == 422

    def test_create_ph_out_of_range(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json={"ph": 15.0, "sampled_at": "2026-03-20T10:00:00"},
        )
        assert resp.status_code == 422

    def test_create_farm_not_found(self, client):
        resp = client.post(
            "/api/farms/9999/fields/1/soil",
            json={"sampled_at": "2026-03-20T10:00:00"},
        )
        assert resp.status_code == 404

    def test_create_field_not_found(self, client, farm_and_field):
        farm_id, _ = farm_and_field
        resp = client.post(
            f"/api/farms/{farm_id}/fields/9999/soil",
            json={"sampled_at": "2026-03-20T10:00:00"},
        )
        assert resp.status_code == 404


# ── List ──────────────────────────────────────────────────────────────

class TestListSoilAnalyses:
    def test_list_empty(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/soil")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json={"sampled_at": "2026-03-01T10:00:00", "ph": 6.0},
        )
        client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json={"sampled_at": "2026-03-15T10:00:00", "ph": 7.0},
        )
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/soil")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Most recent first
        assert data[0]["ph"] == 7.0

    def test_list_field_not_found(self, client, farm_and_field):
        farm_id, _ = farm_and_field
        resp = client.get(f"/api/farms/{farm_id}/fields/9999/soil")
        assert resp.status_code == 404


# ── Get Single ────────────────────────────────────────────────────────

class TestGetSoilAnalysis:
    def test_get_existing(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        create = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json=SAMPLE_SOIL,
        )
        soil_id = create.json()["id"]
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/soil/{soil_id}")
        assert resp.status_code == 200
        assert resp.json()["ph"] == 6.5

    def test_get_not_found(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/soil/9999")
        assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────────────────

class TestUpdateSoilAnalysis:
    def test_update_partial(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        create = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json=SAMPLE_SOIL,
        )
        soil_id = create.json()["id"]
        resp = client.put(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/{soil_id}",
            json={"ph": 7.2, "recommendations": "Add compost to raise organic matter"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ph"] == 7.2
        assert data["recommendations"] == "Add compost to raise organic matter"
        assert data["texture"] == "loam"  # unchanged

    def test_update_not_found(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        resp = client.put(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/9999",
            json={"ph": 7.0},
        )
        assert resp.status_code == 404

    def test_update_validation(self, client, farm_and_field):
        farm_id, field_id = farm_and_field
        create = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json=SAMPLE_SOIL,
        )
        soil_id = create.json()["id"]
        resp = client.put(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/{soil_id}",
            json={"ph": -1.0},
        )
        assert resp.status_code == 422
