"""Tests for region-aware recommendation context — TDD first.

Tests that the recommendation engine injects region metadata (climate zone,
soil type, growing season) and that Jalisco farms get Jalisco-specific advice,
Ontario farms get Ontario-specific advice, and unknown regions get generic fallback.
"""

from datetime import datetime, timedelta

import pytest


# ── Pure service tests: region metadata resolver ──────────────────────────


class TestGetRegionProfile:
    """Test the pure region resolver function."""

    def test_jalisco_returns_tropical_profile(self):
        from cultivos.services.intelligence.regions import get_region_profile

        profile = get_region_profile(state="Jalisco", country="MX")
        assert profile["climate_zone"] == "tropical_subtropical"
        assert "volcanic" in profile["soil_type"].lower()
        assert profile["currency"] == "MXN"
        assert "maiz" in profile["key_crops"]
        assert "agave" in profile["key_crops"]

    def test_ontario_returns_temperate_profile(self):
        from cultivos.services.intelligence.regions import get_region_profile

        profile = get_region_profile(state="Ontario", country="CA")
        assert profile["climate_zone"] == "temperate_continental"
        assert "glacial" in profile["soil_type"].lower()
        assert profile["currency"] == "CAD"
        assert "corn" in profile["key_crops"] or "maiz" in profile["key_crops"]

    def test_unknown_region_returns_generic_profile(self):
        from cultivos.services.intelligence.regions import get_region_profile

        profile = get_region_profile(state="Unknown", country="XX")
        assert profile["climate_zone"] == "generic"
        assert profile["region_name"] == "generic"
        # Generic profile should still have all required keys
        required = {"region_name", "climate_zone", "soil_type", "growing_season",
                    "key_crops", "currency", "seasonal_notes"}
        assert required.issubset(profile.keys())

    def test_jalisco_growing_season_temporal_secas(self):
        from cultivos.services.intelligence.regions import get_region_profile

        profile = get_region_profile(state="Jalisco", country="MX")
        season = profile["growing_season"]
        assert "temporal" in season.lower() or "jun" in season.lower()

    def test_ontario_growing_season_short(self):
        from cultivos.services.intelligence.regions import get_region_profile

        profile = get_region_profile(state="Ontario", country="CA")
        season = profile["growing_season"]
        assert "may" in season.lower() or "sep" in season.lower()

    def test_case_insensitive_matching(self):
        from cultivos.services.intelligence.regions import get_region_profile

        profile = get_region_profile(state="jalisco", country="mx")
        assert profile["climate_zone"] == "tropical_subtropical"


# ── Pure service tests: region-enriched recommendations ──────────────────


class TestRegionEnrichedRecommendations:
    """Test that recommend_treatment uses region context."""

    def test_jalisco_recommendations_mention_region_context(self):
        from cultivos.services.intelligence.recommendations import (
            recommend_treatment, RegionInput,
        )

        result = recommend_treatment(
            health_score=40,
            soil={"ph": 8.5, "organic_matter_pct": 1.0, "nitrogen_ppm": 5},
            crop_type="maiz",
            region=RegionInput(
                region_name="jalisco",
                climate_zone="tropical_subtropical",
                soil_type="Suelos volcanicos (andosoles)",
                growing_season="Temporal Jun-Oct / Secas Nov-May",
                key_crops=["maiz", "agave", "berries", "aguacate"],
                currency="MXN",
                seasonal_notes="Lluvias intensas Jun-Sep, sequia Nov-Abr",
            ),
        )
        # At least one recommendation should have region context in contexto_regional
        assert any(r.get("contexto_regional") for r in result)

    def test_ontario_recommendations_use_cad_currency(self):
        from cultivos.services.intelligence.recommendations import (
            recommend_treatment, RegionInput,
        )

        result = recommend_treatment(
            health_score=40,
            soil={"ph": 5.0, "organic_matter_pct": 1.0, "nitrogen_ppm": 5},
            crop_type="corn",
            region=RegionInput(
                region_name="ontario",
                climate_zone="temperate_continental",
                soil_type="Glacial till soils",
                growing_season="May-Sep (short)",
                key_crops=["corn", "soy", "greenhouse"],
                currency="CAD",
                seasonal_notes="Frost risk before May and after Sep",
            ),
        )
        # Cost field should reflect CAD when Ontario region is provided
        assert any(r.get("costo_estimado_cad") is not None for r in result)

    def test_no_region_still_works(self):
        """Backward compatibility — no region = current behavior."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        result = recommend_treatment(
            health_score=40,
            soil={"ph": 8.5, "organic_matter_pct": 1.0},
            crop_type="maiz",
        )
        assert len(result) >= 1
        # No contexto_regional when no region
        assert all(r.get("contexto_regional") is None for r in result)


# ── API integration tests ────────────────────────────────────────────────


class TestFarmRecommendationsEndpoint:
    """Test GET /api/farms/{farm_id}/recommendations."""

    def _seed_farm_with_health(self, db, state="Jalisco", country="MX", crop="maiz", health_score=40.0):
        """Helper to create farm + field + health score."""
        from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis

        farm = Farm(name="Test Farm", state=state, country=country)
        db.add(farm)
        db.flush()

        field = Field(farm_id=farm.id, name="Field 1", crop_type=crop, hectares=10)
        db.add(field)
        db.flush()

        soil = SoilAnalysis(
            field_id=field.id, ph=8.0, organic_matter_pct=1.5,
            nitrogen_ppm=10, phosphorus_ppm=8, potassium_ppm=60,
            moisture_pct=12, sampled_at=datetime.utcnow(),
        )
        db.add(soil)

        hs = HealthScore(
            field_id=field.id, score=health_score,
            scored_at=datetime.utcnow(),
        )
        db.add(hs)
        db.commit()
        return farm, field

    def test_jalisco_farm_gets_jalisco_recommendations(self, client, db):
        farm, _ = self._seed_farm_with_health(db, state="Jalisco", country="MX")
        resp = client.get(f"/api/farms/{farm.id}/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert "region" in data
        assert data["region"]["climate_zone"] == "tropical_subtropical"
        assert len(data["recommendations"]) >= 1
        # At least one rec has regional context
        assert any(r.get("contexto_regional") for r in data["recommendations"])

    def test_ontario_farm_gets_ontario_recommendations(self, client, db):
        farm, _ = self._seed_farm_with_health(db, state="Ontario", country="CA", crop="corn")
        resp = client.get(f"/api/farms/{farm.id}/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["region"]["climate_zone"] == "temperate_continental"
        assert any(r.get("costo_estimado_cad") is not None for r in data["recommendations"])

    def test_unknown_region_gets_generic_fallback(self, client, db):
        farm, _ = self._seed_farm_with_health(db, state="Desconocido", country="XX")
        resp = client.get(f"/api/farms/{farm.id}/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["region"]["climate_zone"] == "generic"
        assert len(data["recommendations"]) >= 1

    def test_farm_not_found_returns_404(self, client, db):
        resp = client.get("/api/farms/9999/recommendations")
        assert resp.status_code == 404

    def test_no_health_score_returns_422(self, client, db):
        from cultivos.db.models import Farm, Field

        farm = Farm(name="Empty Farm", state="Jalisco", country="MX")
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Empty Field", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/recommendations")
        assert resp.status_code == 422

    def test_multiple_fields_aggregated(self, client, db):
        """Farm with 2 fields should get recommendations for both."""
        from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis

        farm = Farm(name="Multi Farm", state="Jalisco", country="MX")
        db.add(farm)
        db.flush()

        for i, (crop, score) in enumerate([("maiz", 35.0), ("agave", 50.0)]):
            field = Field(farm_id=farm.id, name=f"Field {i+1}", crop_type=crop, hectares=5)
            db.add(field)
            db.flush()
            db.add(SoilAnalysis(
                field_id=field.id, ph=8.0, organic_matter_pct=1.0,
                nitrogen_ppm=5, phosphorus_ppm=5, potassium_ppm=50,
                moisture_pct=10, sampled_at=datetime.utcnow(),
            ))
            db.add(HealthScore(field_id=field.id, score=score, scored_at=datetime.utcnow()))

        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        # Should have recommendations from both fields
        field_names = {r["field_name"] for r in data["recommendations"]}
        assert len(field_names) == 2
