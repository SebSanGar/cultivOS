"""Tests for TEK-enhanced treatment recommendations — ancestral knowledge integration.

TDD: these tests are written FIRST and should FAIL until implementation is complete.
"""

from datetime import datetime


# ── Pure service tests ──────────────────────────────────────────────────


class TestMatchAncestralMethod:
    """Test the pure matching function that links treatments to ancestral methods."""

    def _get_ancestral_data(self):
        """Return seed-like ancestral method dicts for testing."""
        return [
            {
                "name": "Milpa",
                "practice_type": "intercropping",
                "crops": ["maiz", "frijol", "calabaza"],
                "benefits_es": "Fijacion biologica de nitrogeno, control natural de malezas.",
                "scientific_basis": "Validado por FAO e INIFAP.",
            },
            {
                "name": "Abonos verdes ancestrales",
                "practice_type": "soil_management",
                "crops": ["maiz", "frijol", "calabaza", "sorgo"],
                "benefits_es": "Fijacion biologica de nitrogeno (80-200 kg N/ha).",
                "scientific_basis": "Mucuna pruriens fija hasta 200 kg N/ha segun CIMMYT.",
            },
            {
                "name": "Labranza cero tradicional",
                "practice_type": "soil_management",
                "crops": ["maiz", "frijol", "calabaza", "agave"],
                "benefits_es": "Conservacion de estructura del suelo, retencion de humedad.",
                "scientific_basis": "CIMMYT demuestra incremento de materia organica 0.2-0.5% en 5 anos.",
            },
            {
                "name": "Terrazas de cultivo",
                "practice_type": "soil_management",
                "crops": ["maiz", "frijol", "agave", "nopal"],
                "benefits_es": "Prevencion de erosion, retencion de agua de lluvia.",
                "scientific_basis": "CONABIO documenta reduccion de erosion hasta 90%.",
            },
            {
                "name": "Chinampa",
                "practice_type": "water_management",
                "crops": ["maiz", "frijol", "calabaza", "chile", "tomate", "flores"],
                "benefits_es": "Riego pasivo, reciclaje de materia organica acuatica.",
                "scientific_basis": "UNESCO Patrimonio de la Humanidad.",
            },
            {
                "name": "Cultivo en callejones",
                "practice_type": "intercropping",
                "crops": ["maiz", "frijol", "calabaza", "chile"],
                "benefits_es": "Aporte continuo de nitrogeno.",
                "scientific_basis": "ICRAF confirma leucaena aporta 100-300 kg N/ha/ano.",
            },
        ]

    def test_low_organic_matter_matches_soil_management(self):
        """Low organic matter treatment should match soil_management ancestral methods."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        ancestral = self._get_ancestral_data()
        result = recommend_treatment(
            health_score=30,
            soil={"ph": 6.5, "organic_matter_pct": 0.8},
            crop_type="maiz",
            ancestral_methods=ancestral,
        )
        # Find the low organic matter recommendation
        om_rec = [r for r in result if "organica" in r["problema"].lower() or "materia" in r["problema"].lower()]
        assert len(om_rec) >= 1, "Should have a low organic matter recommendation"
        rec = om_rec[0]
        assert rec.get("metodo_ancestral") is not None, "Should have an ancestral method match"
        assert rec["metodo_ancestral"] in ["Abonos verdes ancestrales", "Labranza cero tradicional"]

    def test_low_nitrogen_matches_intercropping_or_green_manure(self):
        """Low nitrogen treatment should match milpa/intercropping or abonos verdes."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        ancestral = self._get_ancestral_data()
        result = recommend_treatment(
            health_score=30,
            soil={"ph": 6.5, "organic_matter_pct": 3.0, "nitrogen_ppm": 5},
            crop_type="maiz",
            ancestral_methods=ancestral,
        )
        n_rec = [r for r in result if "nitrogeno" in r["problema"].lower()]
        assert len(n_rec) >= 1, "Should have a nitrogen deficiency recommendation"
        rec = n_rec[0]
        assert rec.get("metodo_ancestral") is not None
        # Milpa or abonos verdes or cultivo en callejones all fix nitrogen
        assert rec["metodo_ancestral"] in ["Milpa", "Abonos verdes ancestrales", "Cultivo en callejones"]

    def test_low_moisture_matches_water_or_soil_management(self):
        """Low moisture treatment should match water_management or terrazas."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        ancestral = self._get_ancestral_data()
        result = recommend_treatment(
            health_score=40,
            soil={"ph": 6.5, "organic_matter_pct": 3.0, "moisture_pct": 5},
            crop_type="maiz",
            ancestral_methods=ancestral,
        )
        moisture_rec = [r for r in result if "humedad" in r["problema"].lower()]
        assert len(moisture_rec) >= 1
        rec = moisture_rec[0]
        assert rec.get("metodo_ancestral") is not None
        assert rec["metodo_ancestral"] in ["Terrazas de cultivo", "Chinampa", "Labranza cero tradicional"]

    def test_no_matching_ancestral_method_returns_none(self):
        """When no ancestral method matches, fields should be None."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        # Empty ancestral list — no matches possible
        result = recommend_treatment(
            health_score=30,
            soil={"ph": 8.5},
            crop_type="maiz",
            ancestral_methods=[],
        )
        assert len(result) >= 1
        for rec in result:
            assert rec.get("metodo_ancestral") is None
            assert rec.get("base_cientifica") is None

    def test_crop_type_filters_ancestral_matches(self):
        """Ancestral method must list the field's crop in its crops array to match."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        ancestral = self._get_ancestral_data()
        # Aguacate is NOT in milpa's crops list
        result = recommend_treatment(
            health_score=30,
            soil={"ph": 6.5, "organic_matter_pct": 3.0, "nitrogen_ppm": 5},
            crop_type="aguacate",
            ancestral_methods=ancestral,
        )
        n_rec = [r for r in result if "nitrogeno" in r["problema"].lower()]
        assert len(n_rec) >= 1
        rec = n_rec[0]
        # Milpa does not include aguacate — should NOT match milpa
        if rec.get("metodo_ancestral") is not None:
            assert rec["metodo_ancestral"] != "Milpa"

    def test_ancestral_fields_in_treatment_output(self):
        """Treatment dict should have metodo_ancestral, base_cientifica, and razon_match keys."""
        from cultivos.services.intelligence.recommendations import recommend_treatment

        ancestral = self._get_ancestral_data()
        result = recommend_treatment(
            health_score=30,
            soil={"ph": 6.5, "organic_matter_pct": 0.5, "nitrogen_ppm": 5},
            crop_type="maiz",
            ancestral_methods=ancestral,
        )
        for rec in result:
            assert "metodo_ancestral" in rec, "Treatment must have metodo_ancestral key"
            assert "base_cientifica" in rec, "Treatment must have base_cientifica key"
            assert "razon_match" in rec, "Treatment must have razon_match key"


# ── API integration tests ───────────────────────────────────────────────


class TestTEKTreatmentAPI:
    """Test that the API returns ancestral method data with treatment recommendations."""

    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Finca TEK", owner_name="Juan")
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Parcela Milpa", crop_type="maiz", hectares=3)
        db.add(field)
        db.commit()
        db.refresh(field)
        return farm.id, field.id

    def _seed_health_and_soil(self, db, field_id):
        from cultivos.db.models import HealthScore, SoilAnalysis
        hs = HealthScore(
            field_id=field_id, score=25,
            trend="declining", sources=["ndvi", "soil"],
            breakdown={"ndvi": 20.0, "soil": 30.0},
        )
        db.add(hs)
        soil = SoilAnalysis(
            field_id=field_id, ph=6.5, organic_matter_pct=0.8,
            nitrogen_ppm=5, phosphorus_ppm=8, potassium_ppm=50,
            moisture_pct=12, sampled_at=datetime.utcnow(),
        )
        db.add(soil)
        db.commit()

    def _seed_ancestral_methods(self, db):
        from cultivos.db.seeds import seed_ancestral_methods
        seed_ancestral_methods(db)

    def test_api_returns_ancestral_fields(self, client, db):
        """POST /treatments response should include ancestral method fields."""
        fid, flid = self._seed_farm_field(db)
        self._seed_health_and_soil(db, flid)
        self._seed_ancestral_methods(db)

        resp = client.post(f"/api/farms/{fid}/fields/{flid}/treatments")
        assert resp.status_code == 201
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # At least one recommendation should have an ancestral method match
        has_ancestral = any(r.get("ancestral_method_name") for r in data)
        assert has_ancestral, f"Expected at least one ancestral match, got: {data}"

    def test_api_stores_ancestral_in_db(self, client, db):
        """Ancestral method name should be persisted in TreatmentRecord."""
        from cultivos.db.models import TreatmentRecord
        fid, flid = self._seed_farm_field(db)
        self._seed_health_and_soil(db, flid)
        self._seed_ancestral_methods(db)

        client.post(f"/api/farms/{fid}/fields/{flid}/treatments")

        records = db.query(TreatmentRecord).filter(TreatmentRecord.field_id == flid).all()
        assert len(records) >= 1
        # At least one should have ancestral data saved
        has_saved = any(r.ancestral_method_name for r in records)
        assert has_saved, "Expected at least one TreatmentRecord with ancestral_method_name"
