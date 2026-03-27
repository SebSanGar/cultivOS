"""Tests for weather-aware treatment recommendations.

Covers:
- Recommendations change when forecast has rain vs dry
- Recommendation includes timing advice
- Graceful degradation when no weather data
- API route passes weather data through
"""

import pytest
from cultivos.services.intelligence.recommendations import (
    SoilInput,
    WeatherInput,
    ForecastInput,
    recommend_treatment,
)


# --- Pure function tests ---


class TestWeatherAwareRecommendations:
    """Test that weather data modifies treatment recommendations."""

    def _base_soil(self) -> SoilInput:
        """Soil with low organic matter — triggers organic matter recommendation."""
        return SoilInput(
            ph=6.5,
            organic_matter_pct=1.5,
            nitrogen_ppm=20,
            phosphorus_ppm=15,
            potassium_ppm=100,
            moisture_pct=20,
        )

    def test_rain_forecast_adds_timing_advice(self):
        """When rain is forecast within 3 days, recommendation should include pre-rain timing."""
        weather = WeatherInput(
            temp_c=28.0,
            humidity_pct=70,
            wind_kmh=10,
            description="nublado",
            forecast_3day=[
                ForecastInput(temp_c=25.0, humidity_pct=85, wind_kmh=8, description="lluvia ligera"),
                ForecastInput(temp_c=24.0, humidity_pct=90, wind_kmh=5, description="lluvia"),
                ForecastInput(temp_c=26.0, humidity_pct=75, wind_kmh=10, description="nublado"),
            ],
        )
        recs = recommend_treatment(
            health_score=50.0,
            soil=self._base_soil(),
            weather=weather,
        )
        # Should have the organic matter recommendation with timing advice
        om_recs = [r for r in recs if "organica" in r["problema"].lower() or "materia" in r["problema"].lower()]
        assert len(om_recs) > 0
        # Check that at least one recommendation mentions rain/timing
        all_text = " ".join(r["tratamiento"] + " " + r.get("timing_consejo", "") for r in recs)
        assert "lluvia" in all_text.lower() or "rain" in all_text.lower()

    def test_dry_forecast_no_rain_timing(self):
        """When forecast is dry, no rain-related timing advice."""
        weather = WeatherInput(
            temp_c=35.0,
            humidity_pct=30,
            wind_kmh=15,
            description="despejado",
            forecast_3day=[
                ForecastInput(temp_c=36.0, humidity_pct=25, wind_kmh=18, description="despejado"),
                ForecastInput(temp_c=37.0, humidity_pct=20, wind_kmh=20, description="despejado"),
                ForecastInput(temp_c=35.0, humidity_pct=28, wind_kmh=15, description="despejado"),
            ],
        )
        recs = recommend_treatment(
            health_score=50.0,
            soil=self._base_soil(),
            weather=weather,
        )
        assert len(recs) > 0
        # Dry forecast should trigger drought-resilience advice
        all_text = " ".join(r.get("timing_consejo", "") for r in recs)
        assert "sequia" in all_text.lower() or "sequ" in all_text.lower() or "calor" in all_text.lower()

    def test_rain_delays_foliar_spray(self):
        """Foliar spray should be delayed if rain is within 24h (first forecast day)."""
        # Low nitrogen triggers foliar spray (te de composta)
        soil = SoilInput(
            ph=6.5,
            organic_matter_pct=3.0,
            nitrogen_ppm=7,
            phosphorus_ppm=15,
            potassium_ppm=100,
            moisture_pct=20,
        )
        weather = WeatherInput(
            temp_c=25.0,
            humidity_pct=80,
            wind_kmh=5,
            description="nublado",
            forecast_3day=[
                ForecastInput(temp_c=22.0, humidity_pct=95, wind_kmh=3, description="lluvia fuerte"),
                ForecastInput(temp_c=24.0, humidity_pct=70, wind_kmh=8, description="nublado"),
                ForecastInput(temp_c=26.0, humidity_pct=60, wind_kmh=10, description="despejado"),
            ],
        )
        recs = recommend_treatment(health_score=40.0, soil=soil, weather=weather)
        nitrogen_recs = [r for r in recs if "nitrogeno" in r["problema"].lower()]
        assert len(nitrogen_recs) > 0
        # Timing advice should mention delay due to rain
        timing = nitrogen_recs[0].get("timing_consejo", "")
        assert "esperar" in timing.lower() or "retrasar" in timing.lower() or "despues" in timing.lower()

    def test_no_weather_data_graceful(self):
        """Recommendations should work fine without weather data (backward compatible)."""
        recs = recommend_treatment(
            health_score=50.0,
            soil=self._base_soil(),
            weather=None,
        )
        assert len(recs) > 0
        # Should still have the organic matter recommendation
        om_recs = [r for r in recs if "organica" in r["problema"].lower() or "materia" in r["problema"].lower()]
        assert len(om_recs) > 0
        # No timing advice when no weather
        for r in recs:
            assert r.get("timing_consejo") is None or r.get("timing_consejo") == ""

    def test_extreme_heat_adds_protection_advice(self):
        """When forecast shows >38C, add heat protection advice."""
        weather = WeatherInput(
            temp_c=38.0,
            humidity_pct=20,
            wind_kmh=25,
            description="despejado",
            forecast_3day=[
                ForecastInput(temp_c=40.0, humidity_pct=15, wind_kmh=30, description="despejado"),
                ForecastInput(temp_c=41.0, humidity_pct=12, wind_kmh=28, description="despejado"),
                ForecastInput(temp_c=39.0, humidity_pct=18, wind_kmh=22, description="despejado"),
            ],
        )
        recs = recommend_treatment(health_score=50.0, soil=self._base_soil(), weather=weather)
        # Should include a heat/drought-specific recommendation
        all_problems = " ".join(r["problema"] for r in recs)
        assert "calor" in all_problems.lower() or "sequia" in all_problems.lower() or "temperatura" in all_problems.lower()

    def test_recommendation_changes_with_forecast(self):
        """Same soil/health but different weather should produce different recommendations."""
        soil = self._base_soil()

        rain_weather = WeatherInput(
            temp_c=25.0, humidity_pct=80, wind_kmh=5, description="nublado",
            forecast_3day=[
                ForecastInput(temp_c=22.0, humidity_pct=90, wind_kmh=3, description="lluvia"),
                ForecastInput(temp_c=23.0, humidity_pct=85, wind_kmh=5, description="lluvia ligera"),
                ForecastInput(temp_c=25.0, humidity_pct=70, wind_kmh=8, description="nublado"),
            ],
        )
        dry_weather = WeatherInput(
            temp_c=35.0, humidity_pct=25, wind_kmh=20, description="despejado",
            forecast_3day=[
                ForecastInput(temp_c=37.0, humidity_pct=20, wind_kmh=22, description="despejado"),
                ForecastInput(temp_c=38.0, humidity_pct=18, wind_kmh=25, description="despejado"),
                ForecastInput(temp_c=36.0, humidity_pct=22, wind_kmh=20, description="despejado"),
            ],
        )
        recs_rain = recommend_treatment(health_score=50.0, soil=soil, weather=rain_weather)
        recs_dry = recommend_treatment(health_score=50.0, soil=soil, weather=dry_weather)

        # Extract all timing advice
        rain_timing = [r.get("timing_consejo", "") for r in recs_rain]
        dry_timing = [r.get("timing_consejo", "") for r in recs_dry]

        # They should differ
        assert rain_timing != dry_timing


class TestWeatherAwareTreatmentAPI:
    """Test that API route passes weather data into recommendation engine."""

    def _seed_farm_field_health(self, client, admin_headers, db):
        """Create farm, field, soil, and health score for treatment generation."""
        from cultivos.db.models import Farm, Field, SoilAnalysis, HealthScore
        from datetime import datetime

        farm = Farm(name="Rancho Clima", location_lat=20.6, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(name="Parcela Lluvia", farm_id=farm.id, crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        soil = SoilAnalysis(
            field_id=field.id,
            ph=6.5,
            organic_matter_pct=1.5,
            nitrogen_ppm=20,
            phosphorus_ppm=15,
            potassium_ppm=100,
            moisture_pct=20,
            sampled_at=datetime(2026, 3, 1),
        )
        db.add(soil)

        health = HealthScore(field_id=field.id, score=50.0, scored_at=datetime(2026, 3, 15))
        db.add(health)
        db.commit()

        return farm.id, field.id

    def test_api_includes_timing_when_weather_exists(self, client, admin_headers, db):
        """When farm has weather records with rain forecast, treatments should include timing."""
        from cultivos.db.models import WeatherRecord
        from datetime import datetime

        farm_id, field_id = self._seed_farm_field_health(client, admin_headers, db)

        # Add weather record with rain forecast
        wr = WeatherRecord(
            farm_id=farm_id,
            temp_c=25.0,
            humidity_pct=80,
            wind_kmh=5,
            description="nublado",
            forecast_3day=[
                {"temp_c": 22.0, "humidity_pct": 90, "wind_kmh": 3, "description": "lluvia"},
                {"temp_c": 24.0, "humidity_pct": 70, "wind_kmh": 8, "description": "nublado"},
                {"temp_c": 26.0, "humidity_pct": 60, "wind_kmh": 10, "description": "despejado"},
            ],
            recorded_at=datetime(2026, 3, 20),
        )
        db.add(wr)
        db.commit()

        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/treatments",
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) > 0
        # At least one record should have timing advice
        has_timing = any(r.get("timing_consejo") for r in data)
        assert has_timing

    def test_api_works_without_weather(self, client, admin_headers, db):
        """Treatments should still work when no weather records exist for the farm."""
        farm_id, field_id = self._seed_farm_field_health(client, admin_headers, db)

        resp = client.post(
            f"/api/farms/{farm_id}/fields/{field_id}/treatments",
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) > 0
