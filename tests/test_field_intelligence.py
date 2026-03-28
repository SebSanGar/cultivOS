"""Tests for GET /api/farms/{id}/fields/{id}/intelligence — comprehensive field intelligence."""

from datetime import datetime, timedelta

import pytest


class TestFieldIntelligence:
    """Comprehensive field intelligence endpoint tests."""

    def _seed_farm_field(self, db):
        """Create a farm and field with planted_at for growth stage."""
        from cultivos.db.models import Farm, Field

        farm = Farm(
            name="Demo Farm", owner_name="Seb",
            location_lat=20.6, location_lon=-103.3,
            total_hectares=50, municipality="Zapopan", state="Jalisco",
        )
        db.add(farm)
        db.flush()

        field = Field(
            farm_id=farm.id, name="Parcela Norte", crop_type="maiz",
            hectares=10, planted_at=datetime.utcnow() - timedelta(days=45),
        )
        db.add(field)
        db.flush()
        return farm, field

    def _seed_all_data(self, db, farm, field):
        """Seed every data type so all intelligence sections are populated."""
        from cultivos.db.models import (
            HealthScore, NDVIResult, ThermalResult, SoilAnalysis,
            MicrobiomeRecord, WeatherRecord, TreatmentRecord,
        )

        hs = HealthScore(
            field_id=field.id, score=72.5, trend="improving",
            sources=["ndvi", "soil", "thermal"], breakdown={"ndvi": 80, "soil": 65, "thermal": 70},
            scored_at=datetime.utcnow(),
        )
        db.add(hs)

        ndvi = NDVIResult(
            field_id=field.id, ndvi_mean=0.65, ndvi_std=0.08,
            ndvi_min=0.3, ndvi_max=0.85, pixels_total=10000,
            stress_pct=12.5, zones=[{"zone": 1, "mean": 0.6}],
            analyzed_at=datetime.utcnow(),
        )
        db.add(ndvi)

        thermal = ThermalResult(
            field_id=field.id, temp_mean=28.5, temp_std=3.2,
            temp_min=22.0, temp_max=35.0, pixels_total=10000,
            stress_pct=15.0, irrigation_deficit=False,
            analyzed_at=datetime.utcnow(),
        )
        db.add(thermal)

        soil = SoilAnalysis(
            field_id=field.id, ph=6.5, organic_matter_pct=3.2,
            nitrogen_ppm=40, phosphorus_ppm=25, potassium_ppm=180,
            texture="loam", moisture_pct=35.0, depth_cm=30,
            sampled_at=datetime.utcnow(),
        )
        db.add(soil)

        micro = MicrobiomeRecord(
            field_id=field.id, respiration_rate=25.0,
            microbial_biomass_carbon=350.0, fungi_bacteria_ratio=1.2,
            classification="healthy", sampled_at=datetime.utcnow(),
        )
        db.add(micro)

        weather = WeatherRecord(
            farm_id=farm.id, temp_c=26.0, humidity_pct=65.0,
            wind_kmh=12.0, rainfall_mm=5.0, description="parcialmente nublado",
            forecast_3day=[{"day": 1, "temp_c": 27, "rain_mm": 0}],
            recorded_at=datetime.utcnow(),
        )
        db.add(weather)

        treatment = TreatmentRecord(
            field_id=field.id, health_score_used=72.5,
            problema="Estres hidrico leve", causa_probable="Riego insuficiente",
            tratamiento="Aumentar riego 20%", costo_estimado_mxn=500,
            urgencia="media", prevencion="Monitoreo de humedad semanal", organic=True,
        )
        db.add(treatment)

        db.commit()

    def test_full_intelligence_all_sections(self, client, db):
        """All sections populated when data exists."""
        farm, field = self._seed_farm_field(db)
        self._seed_all_data(db, farm, field)

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        assert resp.status_code == 200
        data = resp.json()

        # Field metadata
        assert data["field_id"] == field.id
        assert data["field_name"] == "Parcela Norte"
        assert data["crop_type"] == "maiz"

        # All sections present
        assert data["health"] is not None
        assert data["health"]["score"] == 72.5
        assert data["health"]["trend"] == "improving"

        assert data["ndvi"] is not None
        assert data["ndvi"]["ndvi_mean"] == 0.65
        assert data["ndvi"]["stress_pct"] == 12.5

        assert data["thermal"] is not None
        assert data["thermal"]["temp_mean"] == 28.5

        assert data["soil"] is not None
        assert data["soil"]["ph"] == 6.5

        assert data["microbiome"] is not None
        assert data["microbiome"]["classification"] == "healthy"

        assert data["weather"] is not None
        assert data["weather"]["temp_c"] == 26.0

        assert data["growth_stage"] is not None
        assert data["growth_stage"]["stage"] is not None

        assert data["disease_risk"] is not None
        assert data["disease_risk"]["risk_level"] is not None

        assert data["yield_prediction"] is not None
        assert data["yield_prediction"]["kg_per_ha"] > 0

        assert len(data["treatments"]) == 1
        assert data["treatments"][0]["problema"] == "Estres hidrico leve"

        assert data["carbon"] is not None
        assert data["carbon"]["tendencia"] is not None

        assert data["fusion"] is not None
        assert data["fusion"]["confidence"] > 0

    def test_degrades_no_health(self, client, db):
        """Health section is null when no health score exists, other sections still work."""
        farm, field = self._seed_farm_field(db)
        # Only add NDVI — no health score
        from cultivos.db.models import NDVIResult
        db.add(NDVIResult(
            field_id=field.id, ndvi_mean=0.6, ndvi_std=0.1,
            ndvi_min=0.2, ndvi_max=0.8, pixels_total=5000,
            stress_pct=18.0, zones=[], analyzed_at=datetime.utcnow(),
        ))
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        assert resp.status_code == 200
        data = resp.json()

        assert data["health"] is None
        assert data["ndvi"] is not None
        assert data["ndvi"]["ndvi_mean"] == 0.6

    def test_degrades_no_data(self, client, db):
        """All optional sections are null/empty when field has no data."""
        farm, field = self._seed_farm_field(db)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        assert resp.status_code == 200
        data = resp.json()

        assert data["field_id"] == field.id
        assert data["health"] is None
        assert data["ndvi"] is None
        assert data["thermal"] is None
        assert data["soil"] is None
        assert data["microbiome"] is None
        assert data["weather"] is None
        assert data["disease_risk"] is None
        # yield still computes with default health=50 since crop_type + hectares exist
        assert data["yield_prediction"] is not None
        assert data["treatments"] == []
        assert data["carbon"] is None
        assert data["fusion"] is None
        # growth_stage should still work because planted_at is set
        assert data["growth_stage"] is not None

    def test_degrades_no_planted_at(self, client, db):
        """Growth stage is null when no planted_at date."""
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test", owner_name="X", total_hectares=10)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name="Empty", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/intelligence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["growth_stage"] is None

    def test_farm_not_found(self, client, db):
        resp = client.get("/api/farms/999/fields/1/intelligence")
        assert resp.status_code == 404

    def test_field_not_found(self, client, db):
        from cultivos.db.models import Farm
        farm = Farm(name="Test", owner_name="X", total_hectares=10)
        db.add(farm)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/999/intelligence")
        assert resp.status_code == 404
