"""Tests for yield prediction model — TDD first."""

from datetime import datetime


# -- Pure service tests --------------------------------------------------------


class TestPredictYield:
    def test_predict_yield(self):
        """Given crop type, field area, and health score returns estimated kg/ha."""
        from cultivos.services.intelligence.yield_model import predict_yield

        result = predict_yield(crop_type="maiz", hectares=10.0, health_score=75)

        assert isinstance(result, dict)
        assert "kg_per_ha" in result
        assert isinstance(result["kg_per_ha"], (int, float))
        assert result["kg_per_ha"] > 0
        assert "total_kg" in result
        assert result["total_kg"] == result["kg_per_ha"] * 10.0
        assert "crop_type" in result
        assert result["crop_type"] == "maiz"


class TestYieldRanges:
    def test_yield_ranges(self):
        """Prediction includes min/max range (not just point estimate)."""
        from cultivos.services.intelligence.yield_model import predict_yield

        result = predict_yield(crop_type="frijol", hectares=5.0, health_score=70)

        assert "min_kg_per_ha" in result
        assert "max_kg_per_ha" in result
        assert result["min_kg_per_ha"] < result["kg_per_ha"]
        assert result["max_kg_per_ha"] > result["kg_per_ha"]
        assert result["min_kg_per_ha"] > 0


class TestYieldByCrop:
    def test_yield_by_crop(self):
        """Maiz and frijol produce different baseline yields."""
        from cultivos.services.intelligence.yield_model import predict_yield

        maiz = predict_yield(crop_type="maiz", hectares=1.0, health_score=80)
        frijol = predict_yield(crop_type="frijol", hectares=1.0, health_score=80)

        assert maiz["kg_per_ha"] != frijol["kg_per_ha"], (
            "Different crops should have different baseline yields"
        )
        # Maiz typically yields more kg/ha than frijol
        assert maiz["kg_per_ha"] > frijol["kg_per_ha"]


class TestLowHealthReducesYield:
    def test_low_health_reduces_yield(self):
        """Health score <50 reduces predicted yield by >20% vs healthy field."""
        from cultivos.services.intelligence.yield_model import predict_yield

        healthy = predict_yield(crop_type="maiz", hectares=1.0, health_score=90)
        stressed = predict_yield(crop_type="maiz", hectares=1.0, health_score=40)

        reduction_pct = (healthy["kg_per_ha"] - stressed["kg_per_ha"]) / healthy["kg_per_ha"] * 100
        assert reduction_pct > 20, (
            f"Low health should reduce yield by >20%, got {reduction_pct:.1f}%"
        )


# -- API integration tests ----------------------------------------------------


class TestYieldAPI:
    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field, HealthScore

        farm = Farm(
            name="Rancho Piloto",
            owner_name="Test",
            state="Jalisco",
            location_lat=20.6,
            location_lon=-103.3,
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(
            farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=10
        )
        db.add(field)
        db.commit()
        db.refresh(field)

        # Add a health score
        hs = HealthScore(
            field_id=field.id,
            score=75,
            trend="stable",
            sources=["ndvi", "soil"],
            breakdown={"ndvi": 80.0, "soil": 70.0},
        )
        db.add(hs)
        db.commit()

        return farm.id, field.id

    def test_yield_endpoint_returns_prediction(self, client, db):
        """GET /api/farms/{id}/fields/{id}/yield -> yield prediction with ranges."""
        fid, flid = self._seed_farm_field(db)

        resp = client.get(f"/api/farms/{fid}/fields/{flid}/yield")
        assert resp.status_code == 200

        data = resp.json()
        assert data["field_id"] == flid
        assert data["crop_type"] == "maiz"
        assert "kg_per_ha" in data
        assert "min_kg_per_ha" in data
        assert "max_kg_per_ha" in data
        assert "total_kg" in data
        assert data["total_kg"] > 0

    def test_yield_endpoint_no_health_score(self, client, db):
        """Field with no health score uses default (50) — still returns prediction."""
        from cultivos.db.models import Farm, Field

        farm = Farm(name="Rancho Vacio", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(farm_id=farm.id, name="Parcela Sin Datos", crop_type="frijol", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/yield")
        assert resp.status_code == 200

        data = resp.json()
        assert data["kg_per_ha"] > 0
        assert data["nota"]  # should have a note about insufficient data
