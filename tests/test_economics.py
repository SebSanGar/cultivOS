"""Tests for economic impact calculator — TDD first."""

from datetime import datetime


# -- Pure service tests --------------------------------------------------------


class TestCalculateFarmSavings:
    def test_known_inputs_produce_expected_savings(self):
        """A healthy 10ha farm should produce meaningful savings in MXN."""
        from cultivos.services.intelligence.economics import calculate_farm_savings

        result = calculate_farm_savings(
            health_score=80.0,
            hectares=10.0,
            treatment_count=3,
            irrigation_efficiency=0.6,
        )

        assert isinstance(result, dict)
        assert "water_savings_mxn" in result
        assert "fertilizer_savings_mxn" in result
        assert "yield_improvement_mxn" in result
        assert "total_savings_mxn" in result

        # All savings should be positive for a healthy farm
        assert result["water_savings_mxn"] > 0
        assert result["fertilizer_savings_mxn"] > 0
        assert result["yield_improvement_mxn"] > 0
        assert result["total_savings_mxn"] > 0

        # Total should be the sum of components
        expected_total = (
            result["water_savings_mxn"]
            + result["fertilizer_savings_mxn"]
            + result["yield_improvement_mxn"]
        )
        assert result["total_savings_mxn"] == expected_total

    def test_savings_scale_with_hectares(self):
        """Double the hectares should roughly double the savings."""
        from cultivos.services.intelligence.economics import calculate_farm_savings

        small = calculate_farm_savings(
            health_score=70.0, hectares=5.0, treatment_count=2, irrigation_efficiency=0.5
        )
        large = calculate_farm_savings(
            health_score=70.0, hectares=10.0, treatment_count=2, irrigation_efficiency=0.5
        )

        # Large farm savings should be ~2x small (allow ±1 from rounding)
        assert abs(large["total_savings_mxn"] - small["total_savings_mxn"] * 2) <= 2

    def test_zero_hectares_returns_zero(self):
        """A zero-hectare farm should return zero savings everywhere."""
        from cultivos.services.intelligence.economics import calculate_farm_savings

        result = calculate_farm_savings(
            health_score=80.0, hectares=0.0, treatment_count=5, irrigation_efficiency=0.7
        )

        assert result["water_savings_mxn"] == 0
        assert result["fertilizer_savings_mxn"] == 0
        assert result["yield_improvement_mxn"] == 0
        assert result["total_savings_mxn"] == 0

    def test_partial_data_degrades_gracefully(self):
        """Missing optional inputs should still produce a result."""
        from cultivos.services.intelligence.economics import calculate_farm_savings

        # No treatment count, no irrigation data
        result = calculate_farm_savings(
            health_score=60.0, hectares=8.0, treatment_count=0, irrigation_efficiency=None
        )

        assert isinstance(result, dict)
        assert result["total_savings_mxn"] >= 0
        # Water savings use default efficiency when None
        assert "water_savings_mxn" in result

    def test_higher_health_score_means_more_yield_savings(self):
        """A healthier farm should show more yield improvement savings."""
        from cultivos.services.intelligence.economics import calculate_farm_savings

        healthy = calculate_farm_savings(
            health_score=90.0, hectares=10.0, treatment_count=2, irrigation_efficiency=0.5
        )
        stressed = calculate_farm_savings(
            health_score=40.0, hectares=10.0, treatment_count=2, irrigation_efficiency=0.5
        )

        assert healthy["yield_improvement_mxn"] > stressed["yield_improvement_mxn"]

    def test_baseline_reference_414k(self):
        """The $414,000 MXN baseline should be achievable for a typical Jalisco farm (~20ha, good health)."""
        from cultivos.services.intelligence.economics import calculate_farm_savings

        result = calculate_farm_savings(
            health_score=85.0, hectares=20.0, treatment_count=4, irrigation_efficiency=0.5
        )

        # Should be in a reasonable range relative to the 414k MXN reference
        # (414k is per farm/year for a typical operation)
        assert result["total_savings_mxn"] > 100_000, (
            f"20ha healthy farm should save >100k MXN, got {result['total_savings_mxn']}"
        )


# -- API integration tests ----------------------------------------------------


class TestEconomicImpactAPI:
    def _seed_farm_with_fields(self, db):
        from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord

        farm = Farm(
            name="Rancho Economico",
            owner_name="Test",
            state="Jalisco",
            location_lat=20.6,
            location_lon=-103.3,
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(
            farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=15.0
        )
        db.add(field)
        db.commit()
        db.refresh(field)

        # Add health score
        hs = HealthScore(
            field_id=field.id,
            score=78.0,
            trend="improving",
            sources=["ndvi"],
            breakdown={"ndvi": 78.0},
        )
        db.add(hs)

        # Add treatment records
        tr = TreatmentRecord(
            field_id=field.id,
            health_score_used=78.0,
            problema="Deficiencia de nitrogeno",
            causa_probable="Suelo agotado",
            tratamiento="Composta de lombriz",
            prevencion="Rotacion de cultivos y abono verde",
            costo_estimado_mxn=500,
            urgencia="media",
            applied_at=datetime.utcnow(),
        )
        db.add(tr)
        db.commit()

        return farm.id

    def test_economic_impact_endpoint(self, client, db):
        """GET /api/farms/{id}/economic-impact returns savings breakdown."""
        farm_id = self._seed_farm_with_fields(db)

        resp = client.get(f"/api/farms/{farm_id}/economic-impact")
        assert resp.status_code == 200

        data = resp.json()
        assert "water_savings_mxn" in data
        assert "fertilizer_savings_mxn" in data
        assert "yield_improvement_mxn" in data
        assert "total_savings_mxn" in data
        assert "hectares" in data
        assert "nota" in data
        assert data["total_savings_mxn"] > 0

    def test_economic_impact_farm_not_found(self, client, db):
        """Non-existent farm returns 404."""
        resp = client.get("/api/farms/9999/economic-impact")
        assert resp.status_code == 404

    def test_economic_impact_no_fields(self, client, db):
        """Farm with no fields returns zero savings."""
        from cultivos.db.models import Farm

        farm = Farm(name="Rancho Vacio", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.get(f"/api/farms/{farm.id}/economic-impact")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_savings_mxn"] == 0
        assert data["hectares"] == 0
