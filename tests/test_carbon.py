"""Tests for soil carbon tracking — MRV-lite."""

from datetime import datetime, timedelta

import pytest


# ── Pure service tests ──────────────────────────────────────────────

class TestCarbonEstimate:
    """test_carbon_estimate_from_soil — organic matter % → estimated SOC tonnes/ha."""

    def test_typical_soil(self):
        from cultivos.services.intelligence.carbon import estimate_soc
        result = estimate_soc(organic_matter_pct=3.0, depth_cm=30.0)
        # Van Bemmelen factor: OM * 0.58 = SOC%
        # SOC t/ha = SOC% / 100 * depth_m * bulk_density * 10000
        # 3.0 * 0.58 = 1.74% SOC
        # 1.74 / 100 * 0.30 * 1.3 * 10000 = 67.86 t/ha
        assert result["soc_pct"] == pytest.approx(1.74, abs=0.01)
        assert result["soc_tonnes_per_ha"] == pytest.approx(67.86, abs=0.5)

    def test_low_organic_matter(self):
        from cultivos.services.intelligence.carbon import estimate_soc
        result = estimate_soc(organic_matter_pct=1.0, depth_cm=30.0)
        assert result["soc_pct"] == pytest.approx(0.58, abs=0.01)
        assert result["soc_tonnes_per_ha"] > 0

    def test_high_organic_matter(self):
        from cultivos.services.intelligence.carbon import estimate_soc
        result = estimate_soc(organic_matter_pct=8.0, depth_cm=20.0)
        assert result["soc_pct"] == pytest.approx(4.64, abs=0.01)
        assert result["soc_tonnes_per_ha"] > result["soc_pct"]  # always larger

    def test_custom_bulk_density(self):
        from cultivos.services.intelligence.carbon import estimate_soc
        result = estimate_soc(organic_matter_pct=3.0, depth_cm=30.0, bulk_density=1.1)
        # Lower density → less carbon per volume
        assert result["soc_tonnes_per_ha"] < 67.86

    def test_classification_bajo(self):
        from cultivos.services.intelligence.carbon import estimate_soc
        result = estimate_soc(organic_matter_pct=0.5, depth_cm=30.0)
        assert result["clasificacion"] == "bajo"

    def test_classification_adecuado(self):
        from cultivos.services.intelligence.carbon import estimate_soc
        result = estimate_soc(organic_matter_pct=3.0, depth_cm=30.0)
        assert result["clasificacion"] == "adecuado"

    def test_classification_alto(self):
        from cultivos.services.intelligence.carbon import estimate_soc
        result = estimate_soc(organic_matter_pct=6.0, depth_cm=30.0)
        assert result["clasificacion"] == "alto"


class TestCarbonTrend:
    """test_carbon_trend — 3+ soil records → carbon sequestration trend."""

    def test_gaining_trend(self):
        from cultivos.services.intelligence.carbon import compute_carbon_trend
        records = [
            {"organic_matter_pct": 2.0, "depth_cm": 30.0, "sampled_at": "2025-01-01"},
            {"organic_matter_pct": 2.5, "depth_cm": 30.0, "sampled_at": "2025-06-01"},
            {"organic_matter_pct": 3.0, "depth_cm": 30.0, "sampled_at": "2025-12-01"},
        ]
        result = compute_carbon_trend(records)
        assert result["tendencia"] == "ganando"
        assert result["cambio_soc_tonnes_per_ha"] > 0

    def test_losing_trend(self):
        from cultivos.services.intelligence.carbon import compute_carbon_trend
        records = [
            {"organic_matter_pct": 4.0, "depth_cm": 30.0, "sampled_at": "2025-01-01"},
            {"organic_matter_pct": 3.0, "depth_cm": 30.0, "sampled_at": "2025-06-01"},
            {"organic_matter_pct": 2.0, "depth_cm": 30.0, "sampled_at": "2025-12-01"},
        ]
        result = compute_carbon_trend(records)
        assert result["tendencia"] == "perdiendo"
        assert result["cambio_soc_tonnes_per_ha"] < 0

    def test_stable_trend(self):
        from cultivos.services.intelligence.carbon import compute_carbon_trend
        records = [
            {"organic_matter_pct": 3.0, "depth_cm": 30.0, "sampled_at": "2025-01-01"},
            {"organic_matter_pct": 3.05, "depth_cm": 30.0, "sampled_at": "2025-06-01"},
            {"organic_matter_pct": 3.02, "depth_cm": 30.0, "sampled_at": "2025-12-01"},
        ]
        result = compute_carbon_trend(records)
        assert result["tendencia"] == "estable"

    def test_insufficient_data(self):
        from cultivos.services.intelligence.carbon import compute_carbon_trend
        records = [
            {"organic_matter_pct": 3.0, "depth_cm": 30.0, "sampled_at": "2025-01-01"},
        ]
        result = compute_carbon_trend(records)
        assert result["tendencia"] == "datos_insuficientes"

    def test_recommendations_on_losing(self):
        from cultivos.services.intelligence.carbon import compute_carbon_trend
        records = [
            {"organic_matter_pct": 3.0, "depth_cm": 30.0, "sampled_at": "2025-01-01"},
            {"organic_matter_pct": 2.5, "depth_cm": 30.0, "sampled_at": "2025-06-01"},
            {"organic_matter_pct": 2.0, "depth_cm": 30.0, "sampled_at": "2025-12-01"},
        ]
        result = compute_carbon_trend(records)
        assert len(result["recomendaciones"]) > 0
        # All recommendations should be in Spanish
        assert all(isinstance(r, str) for r in result["recomendaciones"])


# ── API endpoint tests ──────────────────────────────────────────────

class TestCarbonAPI:
    """test_carbon_report_spanish — endpoint returns Spanish-language summary."""

    def _create_farm_field(self, client, admin_headers):
        """Helper to create a farm + field."""
        resp = client.post("/api/farms", json={
            "name": "Rancho Test", "owner_name": "Don Manuel",
            "location_lat": 20.6, "location_lon": -103.3,
            "total_hectares": 50, "municipality": "Zapopan"
        }, headers=admin_headers)
        farm_id = resp.json()["id"]
        resp = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Lote Norte", "crop_type": "maiz", "hectares": 10
        }, headers=admin_headers)
        field_id = resp.json()["id"]
        return farm_id, field_id

    def test_carbon_report_with_soil_data(self, client, db, admin_headers):
        """Endpoint returns Spanish carbon report when soil data exists."""
        farm_id, field_id = self._create_farm_field(client, admin_headers)

        # Add soil analyses with organic matter data
        from cultivos.db.models import SoilAnalysis
        for i, om in enumerate([2.0, 2.5, 3.0]):
            sa = SoilAnalysis(
                field_id=field_id,
                organic_matter_pct=om,
                depth_cm=30.0,
                ph=6.5,
                sampled_at=datetime(2025, 1 + i * 4, 1),
            )
            db.add(sa)
        db.commit()

        resp = client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/carbon",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "soc_actual" in data
        assert "tendencia" in data
        assert data["tendencia"] in ("ganando", "estable", "perdiendo")
        # Spanish summary text
        assert "resumen" in data
        assert isinstance(data["resumen"], str)
        assert len(data["resumen"]) > 10

    def test_carbon_report_no_soil_data(self, client, db, admin_headers):
        """Endpoint returns meaningful response with no soil data."""
        farm_id, field_id = self._create_farm_field(client, admin_headers)

        resp = client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/carbon",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tendencia"] == "datos_insuficientes"

    def test_carbon_report_field_not_found(self, client, admin_headers):
        """404 when field doesn't exist."""
        resp = client.get(
            "/api/farms/999/fields/999/carbon",
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_carbon_report_has_recommendations(self, client, db, admin_headers):
        """Endpoint includes regenerative recommendations."""
        farm_id, field_id = self._create_farm_field(client, admin_headers)

        from cultivos.db.models import SoilAnalysis
        # Declining OM → should trigger recommendations
        for i, om in enumerate([4.0, 3.0, 2.0]):
            sa = SoilAnalysis(
                field_id=field_id,
                organic_matter_pct=om,
                depth_cm=30.0,
                ph=6.5,
                sampled_at=datetime(2025, 1 + i * 4, 1),
            )
            db.add(sa)
        db.commit()

        resp = client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/carbon",
            headers=admin_headers,
        )
        data = resp.json()
        assert len(data["recomendaciones"]) > 0
