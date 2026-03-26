"""Tests for Farm and Field CRUD endpoints."""

import pytest


# ── Farm CRUD ─────────────────────────────────────────────────────────

class TestCreateFarm:
    def test_create_farm_minimal(self, client):
        resp = client.post("/api/farms", json={"name": "Rancho El Sol"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Rancho El Sol"
        assert data["state"] == "Jalisco"
        assert data["country"] == "MX"
        assert data["id"] is not None

    def test_create_farm_full(self, client):
        resp = client.post("/api/farms", json={
            "name": "Hacienda Los Agaves",
            "owner_name": "Juan Garcia",
            "location_lat": 20.6597,
            "location_lon": -103.3496,
            "total_hectares": 150.5,
            "municipality": "Tequila",
            "state": "Jalisco",
            "country": "MX",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["owner_name"] == "Juan Garcia"
        assert data["total_hectares"] == 150.5
        assert data["municipality"] == "Tequila"

    def test_create_farm_empty_name_rejected(self, client):
        resp = client.post("/api/farms", json={"name": ""})
        assert resp.status_code == 422

    def test_create_farm_missing_name_rejected(self, client):
        resp = client.post("/api/farms", json={})
        assert resp.status_code == 422


class TestListFarms:
    def test_list_empty(self, client):
        resp = client.get("/api/farms")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created_farms(self, client):
        client.post("/api/farms", json={"name": "Farm A"})
        client.post("/api/farms", json={"name": "Farm B"})
        resp = client.get("/api/farms")
        assert resp.status_code == 200
        names = [f["name"] for f in resp.json()]
        assert "Farm A" in names
        assert "Farm B" in names


class TestGetFarm:
    def test_get_existing(self, client):
        create = client.post("/api/farms", json={"name": "Rancho Norte"})
        farm_id = create.json()["id"]
        resp = client.get(f"/api/farms/{farm_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Rancho Norte"

    def test_get_not_found(self, client):
        resp = client.get("/api/farms/9999")
        assert resp.status_code == 404


class TestUpdateFarm:
    def test_update_name(self, client):
        create = client.post("/api/farms", json={"name": "Old Name"})
        farm_id = create.json()["id"]
        resp = client.put(f"/api/farms/{farm_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_partial(self, client):
        create = client.post("/api/farms", json={
            "name": "Rancho", "owner_name": "Pedro",
        })
        farm_id = create.json()["id"]
        resp = client.put(f"/api/farms/{farm_id}", json={"total_hectares": 200})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_hectares"] == 200
        assert data["owner_name"] == "Pedro"  # unchanged

    def test_update_not_found(self, client):
        resp = client.put("/api/farms/9999", json={"name": "X"})
        assert resp.status_code == 404


# ── Field CRUD ────────────────────────────────────────────────────────

@pytest.fixture
def farm_id(client):
    """Create a farm and return its ID for field tests."""
    resp = client.post("/api/farms", json={"name": "Test Farm"})
    return resp.json()["id"]


class TestCreateField:
    def test_create_field(self, client, farm_id):
        resp = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Parcela Norte",
            "crop_type": "maiz",
            "hectares": 25.0,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Parcela Norte"
        assert data["crop_type"] == "maiz"
        assert data["farm_id"] == farm_id

    def test_create_field_farm_not_found(self, client):
        resp = client.post("/api/farms/9999/fields", json={"name": "X"})
        assert resp.status_code == 404

    def test_create_field_empty_name_rejected(self, client, farm_id):
        resp = client.post(f"/api/farms/{farm_id}/fields", json={"name": ""})
        assert resp.status_code == 422


class TestListFields:
    def test_list_fields_empty(self, client, farm_id):
        resp = client.get(f"/api/farms/{farm_id}/fields")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_fields_returns_created(self, client, farm_id):
        client.post(f"/api/farms/{farm_id}/fields", json={"name": "Field A"})
        client.post(f"/api/farms/{farm_id}/fields", json={"name": "Field B"})
        resp = client.get(f"/api/farms/{farm_id}/fields")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_fields_farm_not_found(self, client):
        resp = client.get("/api/farms/9999/fields")
        assert resp.status_code == 404


class TestGetField:
    def test_get_field(self, client, farm_id):
        create = client.post(f"/api/farms/{farm_id}/fields", json={"name": "Parcela Sur"})
        field_id = create.json()["id"]
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Parcela Sur"

    def test_get_field_not_found(self, client, farm_id):
        resp = client.get(f"/api/farms/{farm_id}/fields/9999")
        assert resp.status_code == 404


class TestUpdateField:
    def test_update_field(self, client, farm_id):
        create = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Parcela", "crop_type": "maiz",
        })
        field_id = create.json()["id"]
        resp = client.put(f"/api/farms/{farm_id}/fields/{field_id}", json={
            "crop_type": "agave",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop_type"] == "agave"
        assert data["name"] == "Parcela"  # unchanged

    def test_update_field_not_found(self, client, farm_id):
        resp = client.put(f"/api/farms/{farm_id}/fields/9999", json={"name": "X"})
        assert resp.status_code == 404
