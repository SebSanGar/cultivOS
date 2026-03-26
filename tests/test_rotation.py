"""Tests for crop rotation planner — TDD first."""

from datetime import datetime


# -- Pure service tests --------------------------------------------------------


class TestRotationSuggestsLegumeAfterCorn:
    def test_field_with_last_crop_maiz_suggests_frijol(self):
        """Field with last_crop=maiz -> suggestions include frijol (nitrogen fixation)."""
        from cultivos.services.intelligence.rotation import plan_rotation

        result = plan_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 3.0, "nitrogen_ppm": 20},
        )

        # Should be a list of seasons
        assert isinstance(result, list)
        assert len(result) >= 3

        # At least one season should suggest a legume (frijol, lenteja, haba, veza)
        all_crops = [s["crop"] for s in result]
        legumes = {"frijol", "lenteja", "haba", "veza", "garbanzo"}
        assert any(c in legumes for c in all_crops), (
            f"No legume suggested after maiz. Got: {all_crops}"
        )


class TestRotationRespectsJaliscoSeasons:
    def test_jalisco_seasons_match_temporal_secas_cycle(self):
        """Recommendations match Jalisco's temporal (Jun-Oct) and secas (Nov-May) cycle."""
        from cultivos.services.intelligence.rotation import plan_rotation

        result = plan_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 3.0},
        )

        # Each season entry should have season field matching Jalisco's cycle
        for entry in result:
            assert "season" in entry
            assert entry["season"] in ("temporal", "secas", "transicion")

        # Should have at least one temporal and one secas season
        seasons = {s["season"] for s in result}
        assert "temporal" in seasons, "Missing temporal (rainy) season"
        assert "secas" in seasons, "Missing secas (dry) season"


class TestRotationConsidersSoilHealth:
    def test_low_organic_matter_suggests_cover_crop(self):
        """Low organic matter -> suggests cover crop before next cash crop."""
        from cultivos.services.intelligence.rotation import plan_rotation

        result = plan_rotation(
            last_crop="maiz",
            region="jalisco",
            soil={"organic_matter_pct": 0.8, "nitrogen_ppm": 5},
        )

        # Should include a cover crop / abono verde in at least one season
        all_crops = [s["crop"] for s in result]
        all_purposes = [s.get("purpose", "") for s in result]
        has_cover = any(
            "cobertura" in p.lower() or "abono verde" in p.lower()
            for p in all_purposes
        ) or any(
            c in ("veza", "trebol", "centeno", "avena") for c in all_crops
        )
        assert has_cover, (
            f"No cover crop suggested for low organic matter. Crops: {all_crops}"
        )


# -- API integration tests ----------------------------------------------------


class TestRotationAPIReturnsPlan:
    def _seed_farm_field_soil(self, db):
        from cultivos.db.models import Farm, Field, SoilAnalysis

        farm = Farm(name="Rancho Piloto", owner_name="Test", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=10)
        db.add(field)
        db.commit()
        db.refresh(field)

        soil = SoilAnalysis(
            field_id=field.id,
            ph=6.5,
            organic_matter_pct=2.5,
            nitrogen_ppm=18,
            phosphorus_ppm=15,
            potassium_ppm=100,
            moisture_pct=25,
            sampled_at=datetime.utcnow(),
        )
        db.add(soil)
        db.commit()

        return farm.id, field.id

    def test_rotation_api_returns_plan_with_3_seasons(self, client, db):
        """GET /api/farms/{id}/fields/{id}/rotation -> rotation plan with 3 seasons."""
        fid, flid = self._seed_farm_field_soil(db)

        resp = client.get(f"/api/farms/{fid}/fields/{flid}/rotation")
        assert resp.status_code == 200

        data = resp.json()
        assert "field_id" in data
        assert data["field_id"] == flid
        assert "plan" in data
        assert isinstance(data["plan"], list)
        assert len(data["plan"]) >= 3

        # Each season entry has required keys
        for season in data["plan"]:
            assert "season" in season
            assert "crop" in season
            assert "reason" in season
