"""Tests for platform-wide CO2e stats on /carbono page."""

from datetime import datetime

from cultivos.db.models import Farm, Field, SoilAnalysis


def _seed_two_farms(db):
    """Seed 2 farms with soil data so platform-wide aggregation has data."""
    farm1 = Farm(name="Rancho Norte", state="Jalisco", total_hectares=30.0)
    farm2 = Farm(name="Rancho Sur", state="Jalisco", total_hectares=20.0)
    db.add_all([farm1, farm2])
    db.flush()

    f1 = Field(farm_id=farm1.id, name="Campo A", hectares=10.0, crop_type="maiz")
    f2 = Field(farm_id=farm2.id, name="Campo B", hectares=15.0, crop_type="agave")
    db.add_all([f1, f2])
    db.flush()

    db.add_all([
        SoilAnalysis(
            field_id=f1.id, ph=6.5, organic_matter_pct=3.0,
            nitrogen_ppm=40.0, phosphorus_ppm=20.0, potassium_ppm=170.0,
            texture="franco", moisture_pct=25.0, sampled_at=datetime(2025, 6, 1),
        ),
        SoilAnalysis(
            field_id=f2.id, ph=5.9, organic_matter_pct=4.0,
            nitrogen_ppm=50.0, phosphorus_ppm=28.0, potassium_ppm=190.0,
            texture="arcilloso", moisture_pct=30.0, sampled_at=datetime(2025, 9, 1),
        ),
    ])
    db.commit()
    return farm1, farm2, f1, f2


class TestPlatformCarbonStatsHTML:
    """Carbon page has platform-wide stats section in HTML."""

    def test_page_has_platform_stats_section(self, client):
        resp = client.get("/carbono")
        assert 'id="platform-carbon-strip"' in resp.text

    def test_platform_strip_has_total_co2e(self, client):
        resp = client.get("/carbono")
        assert 'id="platform-co2e-value"' in resp.text

    def test_platform_strip_has_total_fields(self, client):
        resp = client.get("/carbono")
        assert 'id="platform-fields-value"' in resp.text

    def test_platform_strip_has_total_hectares(self, client):
        resp = client.get("/carbono")
        assert 'id="platform-hectares-value"' in resp.text

    def test_platform_strip_has_avg_soc(self, client):
        resp = client.get("/carbono")
        assert 'id="platform-soc-value"' in resp.text


class TestPlatformCarbonAPI:
    """/api/intel/carbon returns platform-wide aggregation."""

    def test_intel_carbon_returns_totals(self, client, db):
        _seed_two_farms(db)
        resp = client.get("/api/intel/carbon")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_fields"] == 2
        assert data["total_sequestration_tonnes"] > 0
        assert data["total_hectares"] > 0
        assert data["avg_soc_tonnes_per_ha"] > 0

    def test_intel_carbon_empty_db(self, client, db):
        resp = client.get("/api/intel/carbon")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_fields"] == 0
        assert data["total_sequestration_tonnes"] == 0


class TestCarbonJSCallsPlatformEndpoint:
    """carbon.js should call /api/intel/carbon on init."""

    def test_js_references_intel_carbon_endpoint(self, client):
        resp = client.get("/carbon.js")
        assert resp.status_code == 200
        assert "/api/intel/carbon" in resp.text

    def test_js_renders_platform_stats(self, client):
        resp = client.get("/carbon.js")
        assert "platform-co2e-value" in resp.text
        assert "platform-fields-value" in resp.text
