"""Tests for thermal stress detection service and API endpoints."""

import numpy as np
import pytest

from cultivos.services.crop.thermal import compute_thermal_stress


# -- Pure function tests -------------------------------------------------


class TestComputeThermalStressIdentifiesHotZones:
    def test_hot_zones_detected(self):
        """Array with values > 35 C should produce stress_pct > 50%."""
        # 6 out of 9 pixels above 35
        thermal = np.array([
            [36.0, 37.5, 38.0],
            [34.0, 40.0, 36.5],
            [33.0, 39.0, 37.0],
        ])
        result = compute_thermal_stress(thermal)
        assert result["stress_pct"] > 50.0
        assert result["pixels_total"] == 9


class TestComputeThermalStressUniformNoStress:
    def test_uniform_25c_no_stress(self):
        """Uniform 25 C array should produce stress_pct == 0."""
        thermal = np.full((10, 10), 25.0)
        result = compute_thermal_stress(thermal)
        assert result["stress_pct"] == 0.0
        assert result["temp_mean"] == 25.0
        assert result["temp_min"] == 25.0
        assert result["temp_max"] == 25.0


class TestThermalVariationFlag:
    def test_irrigation_deficit_when_variation_high(self):
        """max - min > 5 C should flag irrigation_deficit: true."""
        thermal = np.array([
            [25.0, 31.0],
            [28.0, 30.0],
        ])
        result = compute_thermal_stress(thermal)
        assert result["irrigation_deficit"] is True

    def test_no_irrigation_deficit_when_variation_low(self):
        """max - min <= 5 C should flag irrigation_deficit: false."""
        thermal = np.array([
            [28.0, 30.0],
            [29.0, 31.0],
        ])
        result = compute_thermal_stress(thermal)
        assert result["irrigation_deficit"] is False


# -- API integration test ------------------------------------------------


class TestThermalAPIStoresResult:
    def _create_farm_and_field(self, client, admin_headers):
        farm = client.post("/api/farms", json={"name": "Thermal Farm"}, headers=admin_headers).json()
        field = client.post(
            f"/api/farms/{farm['id']}/fields",
            json={"name": "Parcela Caliente", "crop_type": "agave", "hectares": 3},
        ).json()
        return farm["id"], field["id"]

    def test_post_thermal_stores_result(self, client, admin_headers):
        """POST /api/farms/{id}/fields/{id}/thermal with array stores ThermalResult."""
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        thermal_data = [
            [36.0, 37.5, 38.0],
            [34.0, 40.0, 36.5],
            [33.0, 39.0, 37.0],
        ]
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/thermal",
            json={"thermal_band": thermal_data},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["field_id"] == field_id
        assert data["stress_pct"] > 50.0
        assert data["irrigation_deficit"] is True
        assert data["pixels_total"] == 9
        assert "id" in data
        assert "analyzed_at" in data
