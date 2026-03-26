"""Tests for NDVI processing service and API endpoints."""

import numpy as np
import pytest

from cultivos.services.crop.ndvi import compute_ndvi, compute_ndvi_stats


# ── Pure function tests ──────────────────────────────────────────────


class TestComputeNDVI:
    def test_basic_formula(self):
        """NDVI = (NIR - Red) / (NIR + Red)."""
        nir = np.array([[0.8, 0.6], [0.4, 0.2]])
        red = np.array([[0.2, 0.3], [0.3, 0.4]])
        ndvi = compute_ndvi(nir, red)
        expected = np.array([[0.6, 0.3333], [0.1429, -0.3333]])
        np.testing.assert_array_almost_equal(ndvi, expected, decimal=3)

    def test_division_by_zero(self):
        """Pixels where NIR + Red == 0 should return 0."""
        nir = np.array([[0.0, 0.5]])
        red = np.array([[0.0, 0.5]])
        ndvi = compute_ndvi(nir, red)
        assert ndvi[0, 0] == 0.0
        assert ndvi[0, 1] == 0.0

    def test_clamps_to_valid_range(self):
        """Result must be in [-1, 1]."""
        nir = np.array([[1000.0, 0.0]])
        red = np.array([[0.0, 1000.0]])
        ndvi = compute_ndvi(nir, red)
        assert ndvi[0, 0] == 1.0
        assert ndvi[0, 1] == -1.0

    def test_uniform_healthy_field(self):
        """All high-NIR, low-Red pixels → NDVI near 1."""
        nir = np.full((10, 10), 0.9)
        red = np.full((10, 10), 0.1)
        ndvi = compute_ndvi(nir, red)
        assert np.all(ndvi > 0.7)

    def test_bare_soil(self):
        """Similar NIR and Red → NDVI near 0."""
        nir = np.full((5, 5), 0.25)
        red = np.full((5, 5), 0.20)
        ndvi = compute_ndvi(nir, red)
        assert np.all(ndvi < 0.2)


class TestComputeNDVIStats:
    def test_healthy_field_stats(self):
        """Known healthy field → high mean, low stress."""
        ndvi = np.full((20, 20), 0.75)
        stats = compute_ndvi_stats(ndvi)
        assert stats["ndvi_mean"] == 0.75
        assert stats["ndvi_std"] == 0.0
        assert stats["stress_pct"] == 0.0
        assert stats["pixels_total"] == 400

    def test_stressed_field_stats(self):
        """Known stressed field → high stress_pct."""
        ndvi = np.full((10, 10), 0.15)
        stats = compute_ndvi_stats(ndvi)
        assert stats["ndvi_mean"] == 0.15
        assert stats["stress_pct"] == 100.0

    def test_zone_classification(self):
        """Zones should sum to 100%."""
        ndvi = np.random.uniform(0, 1, (50, 50))
        stats = compute_ndvi_stats(ndvi)
        total_pct = sum(z["percentage"] for z in stats["zones"])
        assert abs(total_pct - 100.0) < 1.0  # rounding tolerance

    def test_negative_pixels_excluded(self):
        """Negative NDVI pixels (water/shadow) excluded from stats."""
        ndvi = np.array([[-0.5, -0.3, 0.6, 0.8]])
        stats = compute_ndvi_stats(ndvi)
        assert stats["pixels_total"] == 2  # only 0.6 and 0.8
        assert stats["ndvi_mean"] == 0.7

    def test_empty_valid_pixels(self):
        """All negative → empty stats, no crash."""
        ndvi = np.array([[-0.5, -1.0]])
        stats = compute_ndvi_stats(ndvi)
        assert stats["pixels_total"] == 0
        assert stats["stress_pct"] == 0.0
        assert stats["zones"] == []

    def test_golden_healthy_score_above_80(self):
        """Golden set: known healthy field → mean > 0.6 (maps to health > 80)."""
        nir = np.full((30, 30), 0.85)
        red = np.full((30, 30), 0.10)
        ndvi = compute_ndvi(nir, red)
        stats = compute_ndvi_stats(ndvi)
        assert stats["ndvi_mean"] > 0.6

    def test_golden_stressed_below_40(self):
        """Golden set: known stressed field → mean < 0.4."""
        nir = np.full((30, 30), 0.30)
        red = np.full((30, 30), 0.25)
        ndvi = compute_ndvi(nir, red)
        stats = compute_ndvi_stats(ndvi)
        assert stats["ndvi_mean"] < 0.4


# ── API integration tests ───────────────────────────────────────────


class TestNDVIAPI:
    """Tests for /api/farms/{farm_id}/fields/{field_id}/ndvi endpoints."""

    def _create_farm_and_field(self, client, admin_headers):
        farm = client.post("/api/farms", json={"name": "Test Farm"}, headers=admin_headers).json()
        field = client.post(
            f"/api/farms/{farm['id']}/fields",
            json={"name": "Parcela Norte", "crop_type": "maiz", "hectares": 5},
        ).json()
        return farm["id"], field["id"]

    def test_analyze_ndvi_healthy(self, client, admin_headers):
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        # Healthy vegetation: high NIR, low Red
        nir = [[0.8, 0.85], [0.9, 0.75]]
        red = [[0.1, 0.12], [0.08, 0.15]]
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/ndvi",
            json={"nir_band": nir, "red_band": red},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["ndvi_mean"] > 0.6
        assert data["stress_pct"] == 0.0
        assert data["pixels_total"] == 4
        assert len(data["zones"]) == 5

    def test_analyze_ndvi_stressed(self, client, admin_headers):
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        # Stressed: similar NIR and Red
        nir = [[0.25, 0.30], [0.28, 0.22]]
        red = [[0.20, 0.25], [0.22, 0.20]]
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/ndvi",
            json={"nir_band": nir, "red_band": red},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["stress_pct"] == 100.0

    def test_analyze_ndvi_dimension_mismatch(self, client, admin_headers):
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/ndvi",
            json={"nir_band": [[1, 2], [3, 4]], "red_band": [[1, 2, 3]]},
        )
        assert resp.status_code == 422

    def test_analyze_ndvi_empty_bands(self, client, admin_headers):
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/ndvi",
            json={"nir_band": [[]], "red_band": [[]]},
        )
        assert resp.status_code == 422

    def test_list_ndvi_results(self, client, admin_headers):
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        # Submit two analyses
        bands = {"nir_band": [[0.8, 0.9]], "red_band": [[0.1, 0.1]]}
        client.post(f"/api/farms/{farm_id}/fields/{field_id}/ndvi", json=bands)
        client.post(f"/api/farms/{farm_id}/fields/{field_id}/ndvi", json=bands)
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_ndvi_result_by_id(self, client, admin_headers):
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        create_resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/ndvi",
            json={"nir_band": [[0.7]], "red_band": [[0.1]]},
        )
        ndvi_id = create_resp.json()["id"]
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi/{ndvi_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == ndvi_id

    def test_get_ndvi_not_found(self, client, admin_headers):
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}/ndvi/9999")
        assert resp.status_code == 404

    def test_ndvi_farm_not_found(self, client):
        resp = client.post(
            "/api/farms/9999/fields/1/ndvi",
            json={"nir_band": [[0.5]], "red_band": [[0.2]]},
        )
        assert resp.status_code == 404

    def test_ndvi_field_not_found(self, client, admin_headers):
        farm = client.post("/api/farms", json={"name": "Test"}, headers=admin_headers).json()
        resp = client.post(
            f"/api/farms/{farm['id']}/fields/9999/ndvi",
            json={"nir_band": [[0.5]], "red_band": [[0.2]]},
        )
        assert resp.status_code == 404

    def test_ndvi_with_flight_id(self, client, admin_headers):
        farm_id, field_id = self._create_farm_and_field(client, admin_headers)
        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/ndvi",
            json={"nir_band": [[0.8]], "red_band": [[0.1]], "flight_id": None},
        )
        assert resp.status_code == 201
        assert resp.json()["flight_id"] is None
