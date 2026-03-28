"""Tests for carbon sequestration dashboard on intel page."""

from datetime import datetime

import pytest


class TestCarbonSummaryService:
    """Pure service: compute_carbon_summary aggregates carbon data across all fields."""

    def test_carbon_summary_with_data(self, db):
        """Returns aggregate carbon metrics when soil data exists across fields."""
        from cultivos.db.models import Farm, Field, SoilAnalysis
        from cultivos.services.intelligence.analytics import compute_carbon_summary

        farm = Farm(name="Rancho Sol", owner_name="Ana", location_lat=20.6,
                    location_lon=-103.3, total_hectares=50, municipality="Zapopan")
        db.add(farm)
        db.flush()

        f1 = Field(name="Norte", farm_id=farm.id, crop_type="maiz", hectares=10)
        f2 = Field(name="Sur", farm_id=farm.id, crop_type="agave", hectares=15)
        db.add_all([f1, f2])
        db.flush()

        # 3 soil records per field (enough for trend)
        for i, om in enumerate([2.0, 2.5, 3.0]):
            db.add(SoilAnalysis(field_id=f1.id, organic_matter_pct=om,
                                depth_cm=30.0, ph=6.5,
                                sampled_at=datetime(2025, 1 + i * 4, 1)))
        for i, om in enumerate([3.0, 3.5, 4.0]):
            db.add(SoilAnalysis(field_id=f2.id, organic_matter_pct=om,
                                depth_cm=30.0, ph=7.0,
                                sampled_at=datetime(2025, 1 + i * 4, 1)))
        db.commit()

        result = compute_carbon_summary(db)
        assert result["total_fields"] == 2
        assert result["total_hectares"] == 25
        assert result["avg_soc_tonnes_per_ha"] > 0
        assert result["total_sequestration_tonnes"] > 0
        assert len(result["fields"]) == 2
        # Each field entry has expected keys
        for field_entry in result["fields"]:
            assert "field_name" in field_entry
            assert "soc_tonnes_per_ha" in field_entry
            assert "tendencia" in field_entry
            assert "clasificacion" in field_entry

    def test_carbon_summary_no_data(self, db):
        """Returns zeros when no soil data exists."""
        from cultivos.services.intelligence.analytics import compute_carbon_summary

        result = compute_carbon_summary(db)
        assert result["total_fields"] == 0
        assert result["avg_soc_tonnes_per_ha"] == 0
        assert result["total_sequestration_tonnes"] == 0
        assert result["fields"] == []

    def test_carbon_summary_partial_data(self, db):
        """Fields without organic_matter_pct are excluded from aggregation."""
        from cultivos.db.models import Farm, Field, SoilAnalysis
        from cultivos.services.intelligence.analytics import compute_carbon_summary

        farm = Farm(name="Rancho Test", owner_name="Luis", location_lat=20.6,
                    location_lon=-103.3, total_hectares=30, municipality="Tequila")
        db.add(farm)
        db.flush()

        f1 = Field(name="Lote A", farm_id=farm.id, crop_type="maiz", hectares=10)
        f2 = Field(name="Lote B", farm_id=farm.id, crop_type="frijol", hectares=10)
        db.add_all([f1, f2])
        db.flush()

        # f1 has soil data with organic matter
        db.add(SoilAnalysis(field_id=f1.id, organic_matter_pct=3.0,
                            depth_cm=30.0, ph=6.5,
                            sampled_at=datetime(2025, 1, 1)))
        # f2 has soil data WITHOUT organic matter
        db.add(SoilAnalysis(field_id=f2.id, organic_matter_pct=None,
                            depth_cm=30.0, ph=6.5,
                            sampled_at=datetime(2025, 1, 1)))
        db.commit()

        result = compute_carbon_summary(db)
        # Only f1 should appear
        assert result["total_fields"] == 1
        assert len(result["fields"]) == 1
        assert result["fields"][0]["field_name"] == "Lote A"


class TestCarbonSummaryAPI:
    """API endpoint: GET /api/intel/carbon returns aggregate carbon metrics."""

    def _seed_farm_with_soil(self, client, db, admin_headers):
        """Create farm + field + soil records."""
        resp = client.post("/api/farms", json={
            "name": "Rancho Carbon", "owner_name": "Don Pedro",
            "location_lat": 20.6, "location_lon": -103.3,
            "total_hectares": 40, "municipality": "Zapopan"
        }, headers=admin_headers)
        farm_id = resp.json()["id"]

        resp = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Lote Norte", "crop_type": "maiz", "hectares": 15
        }, headers=admin_headers)
        field_id = resp.json()["id"]

        from cultivos.db.models import SoilAnalysis
        for i, om in enumerate([2.0, 2.5, 3.0]):
            db.add(SoilAnalysis(field_id=field_id, organic_matter_pct=om,
                                depth_cm=30.0, ph=6.5,
                                sampled_at=datetime(2025, 1 + i * 4, 1)))
        db.commit()
        return farm_id, field_id

    def test_carbon_endpoint_returns_data(self, client, db, admin_headers):
        """GET /api/intel/carbon returns aggregate carbon data."""
        self._seed_farm_with_soil(client, db, admin_headers)
        resp = client.get("/api/intel/carbon", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_fields"] >= 1
        assert data["avg_soc_tonnes_per_ha"] > 0
        assert data["total_sequestration_tonnes"] > 0
        assert "fields" in data

    def test_carbon_endpoint_empty(self, client, admin_headers):
        """GET /api/intel/carbon returns zeros with no soil data."""
        resp = client.get("/api/intel/carbon", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_fields"] == 0
        assert data["fields"] == []

    def test_carbon_endpoint_correct_units(self, client, db, admin_headers):
        """Carbon values are in tonnes CO2e (SOC t/ha * 3.67 for CO2e)."""
        self._seed_farm_with_soil(client, db, admin_headers)
        resp = client.get("/api/intel/carbon", headers=admin_headers)
        data = resp.json()
        # total_sequestration_tonnes should be in CO2e (= SOC * 3.67 * hectares)
        assert data["total_sequestration_tonnes"] > 0
        # Verify field-level breakdown sums to total
        field_total = sum(
            f["soc_tonnes_per_ha"] * f["hectares"] * 3.67
            for f in data["fields"]
        )
        assert abs(data["total_sequestration_tonnes"] - field_total) < 1.0


class TestCarbonFrontend:
    """Frontend: carbon card renders on intel page."""

    def test_intel_page_has_carbon_card(self, client, admin_headers):
        """intel.html contains the carbon sequestration panel."""
        resp = client.get("/intel")
        assert resp.status_code == 200
        html = resp.text
        assert "intel-carbon" in html
        assert "Secuestro de Carbono" in html

    def test_intel_js_has_load_carbon(self, client, admin_headers):
        """intel.js contains the loadCarbon function."""
        resp = client.get("/intel.js")
        assert resp.status_code == 200
        assert "loadCarbon" in resp.text
