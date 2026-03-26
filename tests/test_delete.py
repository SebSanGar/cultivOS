"""Tests for DELETE endpoints — farms, fields, soil, NDVI."""

import pytest


@pytest.fixture
def farm_field_with_data(client):
    """Create farm + field + soil analysis + NDVI result, return all IDs."""
    farm = client.post("/api/farms", json={"name": "Rancho Borrar"})
    farm_id = farm.json()["id"]

    field = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Prueba", "crop_type": "maiz", "hectares": 5,
    })
    field_id = field.json()["id"]

    soil = client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/soil",
        json={
            "ph": 6.5, "organic_matter_pct": 3.0, "nitrogen_ppm": 40.0,
            "phosphorus_ppm": 20.0, "potassium_ppm": 150.0, "texture": "loam",
            "moisture_pct": 25.0, "sampled_at": "2026-03-20T10:00:00",
        },
    )
    soil_id = soil.json()["id"]

    ndvi = client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/ndvi",
        json={
            "nir_band": [[0.8, 0.7], [0.6, 0.9]],
            "red_band": [[0.1, 0.2], [0.3, 0.05]],
        },
    )
    ndvi_id = ndvi.json()["id"]

    return farm_id, field_id, soil_id, ndvi_id


class TestDeleteFarmCascades:
    def test_delete_farm_cascades_fields(self, client, farm_field_with_data):
        """DELETE /api/farms/{id} removes farm and all its fields."""
        farm_id, field_id, _, _ = farm_field_with_data

        resp = client.delete(f"/api/farms/{farm_id}")
        assert resp.status_code == 204

        # Farm gone
        assert client.get(f"/api/farms/{farm_id}").status_code == 404
        # Field gone
        assert client.get(f"/api/farms/{farm_id}/fields/{field_id}").status_code == 404


class TestDeleteFieldCascades:
    def test_delete_field_cascades_soil_and_ndvi(self, client, farm_field_with_data):
        """DELETE field removes its soil analyses and NDVI results."""
        farm_id, field_id, soil_id, ndvi_id = farm_field_with_data

        resp = client.delete(f"/api/farms/{farm_id}/fields/{field_id}")
        assert resp.status_code == 204

        # Field gone
        assert client.get(f"/api/farms/{farm_id}/fields/{field_id}").status_code == 404
        # Soil gone
        assert client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/{soil_id}"
        ).status_code == 404
        # NDVI gone
        assert client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/ndvi/{ndvi_id}"
        ).status_code == 404


class TestDeleteNonexistent:
    def test_delete_nonexistent_farm_returns_404(self, client):
        resp = client.delete("/api/farms/999")
        assert resp.status_code == 404

    def test_delete_nonexistent_field_returns_404(self, client):
        farm = client.post("/api/farms", json={"name": "Rancho Vacio"})
        farm_id = farm.json()["id"]
        resp = client.delete(f"/api/farms/{farm_id}/fields/999")
        assert resp.status_code == 404


class TestDeleteSoilSingle:
    def test_delete_soil_single(self, client, farm_field_with_data):
        """DELETE single soil record, others remain."""
        farm_id, field_id, soil_id, _ = farm_field_with_data

        # Add a second soil record
        soil2 = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/soil",
            json={
                "ph": 7.0, "organic_matter_pct": 2.0, "nitrogen_ppm": 30.0,
                "phosphorus_ppm": 15.0, "potassium_ppm": 120.0, "texture": "clay",
                "moisture_pct": 30.0, "sampled_at": "2026-03-21T10:00:00",
            },
        )
        soil2_id = soil2.json()["id"]

        resp = client.delete(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/{soil_id}"
        )
        assert resp.status_code == 204

        # Deleted record gone
        assert client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/{soil_id}"
        ).status_code == 404
        # Other record still there
        assert client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/soil/{soil2_id}"
        ).status_code == 200
