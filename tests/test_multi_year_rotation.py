"""Tests for multi-year rotation planner — TDD first.

D4: 3-year rotation sequence with soil organic matter projections
and milpa system recommendations for Jalisco.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, SoilAnalysis
from cultivos.db.session import get_db


# -- Pure service tests --------------------------------------------------------


class TestMultiYearPlanReturns6Seasons:
    """3-year plan should produce 6 seasons (alternating secas/temporal)."""

    def test_returns_6_season_entries(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 3.0, "nitrogen_ppm": 20},
        )
        assert len(result["plan"]) == 6

    def test_seasons_alternate_secas_temporal(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 3.0, "nitrogen_ppm": 20},
        )
        seasons = [e["season"] for e in result["plan"]]
        # Should alternate secas, temporal, secas, temporal, secas, temporal
        expected = ["secas", "temporal", "secas", "temporal", "secas", "temporal"]
        assert seasons == expected

    def test_each_entry_has_year_field(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="frijol",
            region="jalisco",
        )
        for entry in result["plan"]:
            assert "year" in entry
            assert isinstance(entry["year"], int)

    def test_years_span_1_to_3(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="frijol",
            region="jalisco",
        )
        years = [e["year"] for e in result["plan"]]
        assert years == [1, 1, 2, 2, 3, 3]


class TestMilpaRecommendation:
    """Milpa (maize+beans+squash) is recommended for Jalisco."""

    def test_milpa_detected_for_jalisco_maiz(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
        )
        assert result["milpa_recommended"] is True

    def test_milpa_includes_three_sisters(self):
        """Milpa plan should include maiz, frijol, and calabaza somewhere."""
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
        )
        crops = {e["crop"] for e in result["plan"]}
        milpa_crops = {"maiz", "frijol", "calabaza"}
        # At least 2 of 3 milpa crops should appear (maiz may not repeat as last_crop)
        assert len(crops & milpa_crops) >= 2, f"Expected milpa crops, got {crops}"

    def test_milpa_description_present(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
        )
        assert "milpa_description" in result
        assert "milpa" in result["milpa_description"].lower()

    def test_milpa_not_recommended_for_aguacate(self):
        """Aguacate (avocado) is a perennial — milpa doesn't apply."""
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="aguacate",
            region="jalisco",
        )
        assert result["milpa_recommended"] is False


class TestSoilOrganicMatterProjection:
    """Each season should project soil OM based on crop type."""

    def test_each_entry_has_om_projection(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 2.0, "nitrogen_ppm": 15},
        )
        for entry in result["plan"]:
            assert "organic_matter_pct" in entry
            assert isinstance(entry["organic_matter_pct"], float)

    def test_cover_crops_increase_om(self):
        """Cover crops (veza, avena) should increase OM projection."""
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 1.5, "nitrogen_ppm": 5},
        )
        # With low OM, first season should be cover crop
        plan = result["plan"]
        # Find a cover crop entry
        cover_entries = [e for e in plan if e["crop"] in ("veza", "trebol", "centeno", "avena")]
        if cover_entries:
            # The OM after a cover crop should be > starting OM
            assert cover_entries[0]["organic_matter_pct"] > 1.5

    def test_heavy_feeders_decrease_om(self):
        """Heavy feeders (maiz, sorgo) should slightly decrease OM."""
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="frijol",
            region="jalisco",
            soil={"organic_matter_pct": 3.5, "nitrogen_ppm": 25},
        )
        plan = result["plan"]
        # Find a heavy feeder entry
        feeder_entries = [e for e in plan if e["crop"] in ("maiz", "sorgo", "calabaza")]
        if feeder_entries:
            # OM should decrease or stay same after heavy feeder (check the NEXT entry's baseline)
            idx = plan.index(feeder_entries[0])
            if idx > 0:
                assert feeder_entries[0]["organic_matter_pct"] <= plan[idx - 1]["organic_matter_pct"]

    def test_3_year_plan_shows_om_recovery(self):
        """Starting from degraded soil, 3-year plan should show OM recovery."""
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 1.0, "nitrogen_ppm": 5},
        )
        plan = result["plan"]
        first_om = plan[0]["organic_matter_pct"]
        last_om = plan[-1]["organic_matter_pct"]
        assert last_om > first_om, f"OM should recover: {first_om} -> {last_om}"

    def test_default_om_when_no_soil_data(self):
        """Without soil data, start from a default OM of 2.5%."""
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
        )
        first_om = result["plan"][0]["organic_matter_pct"]
        # Should be close to 2.5 +/- the first crop's effect
        assert 1.5 < first_om < 4.0


class TestMultiYearSummary:
    """Multi-year result includes summary stats."""

    def test_has_total_years(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(last_crop="maiz", region="jalisco")
        assert result["total_years"] == 3

    def test_has_om_start_and_end(self):
        from cultivos.services.intelligence.rotation import plan_multi_year_rotation

        result = plan_multi_year_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 2.0},
        )
        assert "om_start" in result
        assert "om_end" in result
        assert isinstance(result["om_start"], float)
        assert isinstance(result["om_end"], float)


# -- API integration tests ----------------------------------------------------


@pytest.fixture()
def app(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _seed_farm_field(db, crop_type="maiz", om_pct=2.0, nitrogen=12.0):
    farm = Farm(name="Rancho Multi", owner_name="Test", state="Jalisco", total_hectares=50.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Norte", crop_type=crop_type, hectares=15.0)
    db.add(field)
    db.flush()
    db.add(SoilAnalysis(
        field_id=field.id, ph=6.5, organic_matter_pct=om_pct,
        nitrogen_ppm=nitrogen, phosphorus_ppm=15.0, potassium_ppm=100.0,
        moisture_pct=25.0, sampled_at=datetime(2026, 1, 15),
    ))
    db.commit()
    return farm.id, field.id


class TestMultiYearAPI:
    """GET /api/farms/{id}/fields/{id}/rotation/multi-year returns 3-year plan."""

    def test_returns_200(self, client, db):
        fid, flid = _seed_farm_field(db)
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/rotation/multi-year")
        assert resp.status_code == 200

    def test_response_has_plan_with_6_entries(self, client, db):
        fid, flid = _seed_farm_field(db)
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/rotation/multi-year")
        data = resp.json()
        assert len(data["plan"]) == 6

    def test_response_has_milpa_fields(self, client, db):
        fid, flid = _seed_farm_field(db)
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/rotation/multi-year")
        data = resp.json()
        assert "milpa_recommended" in data
        assert "milpa_description" in data

    def test_response_has_om_projections(self, client, db):
        fid, flid = _seed_farm_field(db)
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/rotation/multi-year")
        data = resp.json()
        for entry in data["plan"]:
            assert "organic_matter_pct" in entry
            assert "year" in entry

    def test_response_has_summary(self, client, db):
        fid, flid = _seed_farm_field(db)
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/rotation/multi-year")
        data = resp.json()
        assert data["total_years"] == 3
        assert "om_start" in data
        assert "om_end" in data

    def test_422_for_no_crop_type(self, client, db):
        farm = Farm(name="No Crop", owner_name="Test", state="Jalisco")
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Empty", hectares=5.0, crop_type=None)
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/rotation/multi-year")
        assert resp.status_code == 422

    def test_404_for_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/fields/1/rotation/multi-year")
        assert resp.status_code == 404

    def test_milpa_for_jalisco_maiz(self, client, db):
        fid, flid = _seed_farm_field(db, crop_type="maiz")
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/rotation/multi-year")
        data = resp.json()
        assert data["milpa_recommended"] is True

    def test_no_milpa_for_aguacate(self, client, db):
        fid, flid = _seed_farm_field(db, crop_type="aguacate")
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/rotation/multi-year")
        data = resp.json()
        assert data["milpa_recommended"] is False
