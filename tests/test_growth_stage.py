"""Tests for crop growth stage tracking — phenology stages per crop type."""

from datetime import datetime, timedelta

import pytest


# ── Pure service tests ─────────────────────────────────────────────────

class TestPhenologyService:
    """Test the pure phenology computation — no HTTP, no DB."""

    def test_compute_stage_siembra(self):
        """A field planted 5 days ago should be in siembra stage."""
        from cultivos.services.crop.phenology import compute_growth_stage
        planted = datetime.utcnow() - timedelta(days=5)
        result = compute_growth_stage("maiz", planted)
        assert result["stage"] == "siembra"
        assert result["stage_es"] == "Siembra"

    def test_compute_stage_vegetativo(self):
        """Maiz planted 30 days ago should be in vegetativo stage."""
        from cultivos.services.crop.phenology import compute_growth_stage
        planted = datetime.utcnow() - timedelta(days=30)
        result = compute_growth_stage("maiz", planted)
        assert result["stage"] == "vegetativo"

    def test_compute_stage_floracion(self):
        """Maiz planted 70 days ago should be in floracion stage."""
        from cultivos.services.crop.phenology import compute_growth_stage
        planted = datetime.utcnow() - timedelta(days=70)
        result = compute_growth_stage("maiz", planted)
        assert result["stage"] == "floracion"

    def test_compute_stage_fructificacion(self):
        """Maiz planted 90 days ago should be in fructificacion stage."""
        from cultivos.services.crop.phenology import compute_growth_stage
        planted = datetime.utcnow() - timedelta(days=90)
        result = compute_growth_stage("maiz", planted)
        assert result["stage"] == "fructificacion"

    def test_compute_stage_cosecha(self):
        """Maiz planted 130 days ago should be in cosecha stage."""
        from cultivos.services.crop.phenology import compute_growth_stage
        planted = datetime.utcnow() - timedelta(days=130)
        result = compute_growth_stage("maiz", planted)
        assert result["stage"] == "cosecha"

    def test_stage_transitions_correctly_by_date(self):
        """Different planted_at dates produce different stages for same crop."""
        from cultivos.services.crop.phenology import compute_growth_stage
        now = datetime.utcnow()
        stages_seen = set()
        for days_ago in [5, 30, 70, 90, 130]:
            planted = now - timedelta(days=days_ago)
            result = compute_growth_stage("maiz", planted)
            stages_seen.add(result["stage"])
        assert len(stages_seen) == 5  # all 5 stages represented

    def test_unknown_crop_uses_defaults(self):
        """Unknown crop type should still return a valid stage."""
        from cultivos.services.crop.phenology import compute_growth_stage
        planted = datetime.utcnow() - timedelta(days=30)
        result = compute_growth_stage("desconocido", planted)
        assert result["stage"] in ("siembra", "vegetativo", "floracion", "fructificacion", "cosecha")

    def test_water_multiplier_varies_by_stage(self):
        """Different growth stages should have different water multipliers."""
        from cultivos.services.crop.phenology import compute_growth_stage
        now = datetime.utcnow()
        multipliers = set()
        for days_ago in [5, 30, 70, 90, 130]:
            planted = now - timedelta(days=days_ago)
            result = compute_growth_stage("maiz", planted)
            multipliers.add(result["water_multiplier"])
        assert len(multipliers) >= 3  # at least 3 distinct multipliers

    def test_nutrient_focus_varies_by_stage(self):
        """Each stage should have nutrient focus info."""
        from cultivos.services.crop.phenology import compute_growth_stage
        planted = datetime.utcnow() - timedelta(days=30)
        result = compute_growth_stage("maiz", planted)
        assert "nutrient_focus" in result
        assert len(result["nutrient_focus"]) > 0

    def test_no_planted_date_returns_none(self):
        """If no planted_at date, should return None."""
        from cultivos.services.crop.phenology import compute_growth_stage
        result = compute_growth_stage("maiz", None)
        assert result is None


# ── Irrigation integration tests ───────────────────────────────────────

class TestIrrigationWithGrowthStage:
    """Test that irrigation schedule adjusts for growth stage."""

    def test_stage_aware_irrigation_differs_from_default(self):
        """Irrigation with growth_stage should differ from without it."""
        from cultivos.services.intelligence.irrigation import compute_irrigation_schedule
        # Default (no growth stage)
        result_default = compute_irrigation_schedule(
            crop_type="maiz", hectares=10, soil=None, weather=None, thermal=None,
        )
        # Flowering stage (high water need)
        result_flowering = compute_irrigation_schedule(
            crop_type="maiz", hectares=10, soil=None, weather=None, thermal=None,
            growth_stage="floracion",
        )
        # Cosecha stage (low water need)
        result_harvest = compute_irrigation_schedule(
            crop_type="maiz", hectares=10, soil=None, weather=None, thermal=None,
            growth_stage="cosecha",
        )
        # Flowering should need more water than harvest
        assert result_flowering["liters_total_per_ha"] > result_harvest["liters_total_per_ha"]

    def test_seedling_stage_needs_moderate_water(self):
        """Siembra stage has moderate water needs (establishing roots)."""
        from cultivos.services.intelligence.irrigation import compute_irrigation_schedule
        result = compute_irrigation_schedule(
            crop_type="maiz", hectares=10, soil=None, weather=None, thermal=None,
            growth_stage="siembra",
        )
        assert result["liters_total_per_ha"] > 0


# ── Recommendation integration tests ──────────────────────────────────

class TestRecommendationsWithGrowthStage:
    """Test that recommendations mention growth stage context."""

    def test_recommendation_mentions_growth_stage(self):
        """When growth_stage is provided, recommendation should reference it."""
        from cultivos.services.intelligence.recommendations import recommend_treatment
        recs = recommend_treatment(
            health_score=50,
            soil={"ph": 7.0, "organic_matter_pct": 1.5, "nitrogen_ppm": 10},
            growth_stage="floracion",
        )
        # At least one recommendation should mention flowering context
        texts = " ".join(r.get("tratamiento", "") + " " + r.get("prevencion", "") for r in recs)
        assert "floracion" in texts.lower() or "floración" in texts.lower()


# ── API endpoint tests ─────────────────────────────────────────────────

class TestGrowthStageAPI:
    """Test the GET growth-stage endpoint."""

    def test_get_growth_stage_with_planted_at(self, client, db, admin_headers):
        """Field with planted_at should return computed growth stage."""
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm")
        db.add(farm)
        db.commit()
        planted = datetime.utcnow() - timedelta(days=30)
        field = Field(farm_id=farm.id, name="Parcela 1", crop_type="maiz", planted_at=planted)
        db.add(field)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-stage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == "vegetativo"
        assert data["crop_type"] == "maiz"
        assert "water_multiplier" in data

    def test_get_growth_stage_no_planted_at(self, client, db, admin_headers):
        """Field without planted_at should return 422."""
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm")
        db.add(farm)
        db.commit()
        field = Field(farm_id=farm.id, name="Parcela 1", crop_type="maiz")
        db.add(field)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/growth-stage")
        assert resp.status_code == 422

    def test_field_create_with_planted_at(self, client, db, admin_headers):
        """Creating a field with planted_at should persist it."""
        from cultivos.db.models import Farm
        farm = Farm(name="Test Farm")
        db.add(farm)
        db.commit()

        resp = client.post(f"/api/farms/{farm.id}/fields", json={
            "name": "Parcela 1",
            "crop_type": "maiz",
            "planted_at": "2026-03-01T00:00:00",
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["planted_at"] is not None

    def test_field_update_planted_at(self, client, db, admin_headers):
        """Updating planted_at on an existing field should work."""
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm")
        db.add(farm)
        db.commit()
        field = Field(farm_id=farm.id, name="Parcela 1", crop_type="maiz")
        db.add(field)
        db.commit()

        resp = client.put(f"/api/farms/{farm.id}/fields/{field.id}", json={
            "planted_at": "2026-02-15T00:00:00",
        })
        assert resp.status_code == 200
        assert resp.json()["planted_at"] is not None
