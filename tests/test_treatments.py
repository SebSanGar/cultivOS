"""Tests for treatment recommendation engine — TDD first."""

from datetime import datetime


# ── Pure service tests ──────────────────────────────────────────────────


class TestRecommendTreatment:
    def test_low_ndvi_high_ph_recommends_sulfur_amendment(self):
        """health score < 40, soil pH > 8.0 -> recommendation includes 'acidificar suelo'."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        result = recommend_treatment(
            health_score=30,
            soil={"ph": 8.5, "organic_matter_pct": 2.0, "nitrogen_ppm": 10},
            crop_type="maiz",
        )
        # Should have at least one recommendation mentioning soil acidification
        problems = [r["problema"] for r in result]
        assert any("acidificar" in p.lower() or "ph" in p.lower() for p in problems)

    def test_healthy_field_returns_no_treatment(self):
        """health score > 80 -> 'Sin tratamiento necesario'."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        result = recommend_treatment(
            health_score=90,
            soil={"ph": 6.5, "organic_matter_pct": 5.0, "nitrogen_ppm": 40},
            crop_type="maiz",
        )
        assert len(result) == 1
        assert result[0]["problema"] == "Sin tratamiento necesario"

    def test_treatment_format_matches_protocol(self):
        """Output has required keys: problema, causa_probable, tratamiento,
        costo_estimado_mxn, urgencia, prevencion."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        result = recommend_treatment(
            health_score=30,
            soil={"ph": 8.5, "organic_matter_pct": 1.0, "nitrogen_ppm": 5},
            crop_type="agave",
        )
        required_keys = {
            "problema", "causa_probable", "tratamiento",
            "costo_estimado_mxn", "urgencia", "prevencion", "organic",
        }
        for rec in result:
            assert required_keys.issubset(rec.keys()), f"Missing keys: {required_keys - rec.keys()}"

    def test_treatment_never_recommends_synthetic(self):
        """All recommendations must have organic: true."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        result = recommend_treatment(
            health_score=20,
            soil={"ph": 4.0, "organic_matter_pct": 0.5, "nitrogen_ppm": 3,
                  "phosphorus_ppm": 2, "potassium_ppm": 30},
            crop_type="aguacate",
        )
        for rec in result:
            if rec["problema"] == "Sin tratamiento necesario":
                continue
            assert rec["organic"] is True, f"Non-organic recommendation found: {rec['tratamiento']}"


# ── API integration tests ───────────────────────────────────────────────


class TestTreatmentAPI:
    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm", owner_name="Test Owner")
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Test Field", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)
        return farm.id, field.id

    def _seed_health_and_soil(self, db, field_id, score=30, ph=8.5, om=1.0):
        from cultivos.db.models import HealthScore, SoilAnalysis
        hs = HealthScore(
            field_id=field_id, score=score,
            trend="declining", sources=["ndvi", "soil"],
            breakdown={"ndvi": 25.0, "soil": 35.0, "trend": 20.0},
        )
        db.add(hs)
        soil = SoilAnalysis(
            field_id=field_id, ph=ph, organic_matter_pct=om,
            nitrogen_ppm=10, phosphorus_ppm=8, potassium_ppm=50,
            moisture_pct=15, sampled_at=datetime.utcnow(),
        )
        db.add(soil)
        db.commit()

    def test_treatment_api_crud(self, client, db):
        """POST /api/farms/{id}/fields/{id}/treatments returns treatment, GET lists them."""
        fid, flid = self._seed_farm_field(db)
        self._seed_health_and_soil(db, flid)

        # POST to generate treatments
        resp = client.post(f"/api/farms/{fid}/fields/{flid}/treatments")
        assert resp.status_code == 201
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Each has required keys
        for rec in data:
            assert "problema" in rec
            assert "tratamiento" in rec

        # GET to list stored treatments
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/treatments")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
