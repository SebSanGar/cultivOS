"""Tests for irrigation optimization — TDD first."""

from datetime import datetime


# -- Pure service tests --------------------------------------------------------


class TestIrrigationRecommendsLessAfterRain:
    def test_recent_rainfall_skips_irrigation(self):
        """Recent rainfall > 10mm -> skip next irrigation."""
        from cultivos.services.intelligence.irrigation import compute_irrigation_schedule

        result = compute_irrigation_schedule(
            crop_type="maiz",
            hectares=10.0,
            soil={"texture": "loam", "moisture_pct": 45.0},
            weather={"temp_c": 28.0, "humidity_pct": 70.0, "recent_rainfall_mm": 15.0},
            thermal=None,
        )

        assert isinstance(result, dict)
        assert "schedule" in result
        assert isinstance(result["schedule"], list)
        # With >10mm recent rain, daily liters should be reduced or skipped
        total_liters = sum(day["liters_per_ha"] for day in result["schedule"])
        # Compare against a no-rain scenario
        result_no_rain = compute_irrigation_schedule(
            crop_type="maiz",
            hectares=10.0,
            soil={"texture": "loam", "moisture_pct": 25.0},
            weather={"temp_c": 28.0, "humidity_pct": 70.0, "recent_rainfall_mm": 0.0},
            thermal=None,
        )
        total_liters_no_rain = sum(day["liters_per_ha"] for day in result_no_rain["schedule"])
        assert total_liters < total_liters_no_rain, (
            f"Rain should reduce irrigation: {total_liters} >= {total_liters_no_rain}"
        )


class TestIrrigationIncreasesInDrought:
    def test_no_rain_high_temp_increases_frequency(self):
        """No rain forecast + high temp -> increase irrigation frequency."""
        from cultivos.services.intelligence.irrigation import compute_irrigation_schedule

        # Normal conditions
        normal = compute_irrigation_schedule(
            crop_type="maiz",
            hectares=10.0,
            soil={"texture": "loam", "moisture_pct": 30.0},
            weather={"temp_c": 25.0, "humidity_pct": 60.0, "recent_rainfall_mm": 5.0},
            thermal=None,
        )

        # Drought conditions: high temp, no rain, low humidity
        drought = compute_irrigation_schedule(
            crop_type="maiz",
            hectares=10.0,
            soil={"texture": "loam", "moisture_pct": 15.0},
            weather={"temp_c": 38.0, "humidity_pct": 20.0, "recent_rainfall_mm": 0.0},
            thermal={"stress_pct": 60.0, "irrigation_deficit": True},
        )

        normal_total = sum(day["liters_per_ha"] for day in normal["schedule"])
        drought_total = sum(day["liters_per_ha"] for day in drought["schedule"])
        assert drought_total > normal_total, (
            f"Drought should increase irrigation: {drought_total} <= {normal_total}"
        )
        assert drought["urgencia"] in ("alta", "media"), (
            f"Drought should flag high urgency, got: {drought['urgencia']}"
        )


class TestIrrigationConsidersSoilMoisture:
    def test_sandy_soil_needs_more_water(self):
        """Sandy soil drains faster, needs more frequent irrigation than clay."""
        from cultivos.services.intelligence.irrigation import compute_irrigation_schedule

        sandy = compute_irrigation_schedule(
            crop_type="maiz",
            hectares=10.0,
            soil={"texture": "sand", "moisture_pct": 20.0},
            weather={"temp_c": 30.0, "humidity_pct": 50.0, "recent_rainfall_mm": 0.0},
            thermal=None,
        )

        clay = compute_irrigation_schedule(
            crop_type="maiz",
            hectares=10.0,
            soil={"texture": "clay", "moisture_pct": 20.0},
            weather={"temp_c": 30.0, "humidity_pct": 50.0, "recent_rainfall_mm": 0.0},
            thermal=None,
        )

        sandy_total = sum(day["liters_per_ha"] for day in sandy["schedule"])
        clay_total = sum(day["liters_per_ha"] for day in clay["schedule"])
        assert sandy_total > clay_total, (
            f"Sandy soil should need more water than clay: {sandy_total} <= {clay_total}"
        )


# -- API integration tests ----------------------------------------------------


class TestIrrigationAPIReturnsSchedule:
    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field, SoilAnalysis, WeatherRecord

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

        # Add soil analysis
        soil = SoilAnalysis(
            field_id=field.id,
            ph=6.5,
            organic_matter_pct=2.5,
            nitrogen_ppm=18,
            phosphorus_ppm=15,
            potassium_ppm=100,
            texture="loam",
            moisture_pct=25.0,
            sampled_at=datetime.utcnow(),
        )
        db.add(soil)

        # Add weather record
        weather = WeatherRecord(
            farm_id=farm.id,
            temp_c=30.0,
            humidity_pct=50.0,
            wind_kmh=10.0,
            description="soleado",
            forecast_3day=[],
        )
        db.add(weather)
        db.commit()

        return farm.id, field.id

    def test_irrigation_api_returns_daily_schedule(self, client, db):
        """GET /api/farms/{id}/fields/{id}/irrigation -> daily schedule with liters/ha."""
        fid, flid = self._seed_farm_field(db)

        resp = client.get(f"/api/farms/{fid}/fields/{flid}/irrigation")
        assert resp.status_code == 200

        data = resp.json()
        assert "field_id" in data
        assert data["field_id"] == flid
        assert "schedule" in data
        assert isinstance(data["schedule"], list)
        assert len(data["schedule"]) >= 1

        # Each day entry has required keys
        for day in data["schedule"]:
            assert "day" in day
            assert "liters_per_ha" in day
            assert isinstance(day["liters_per_ha"], (int, float))
            assert day["liters_per_ha"] >= 0
