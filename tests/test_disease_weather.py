"""Tests for disease-weather risk assessment — fungal risk from humidity + rainfall.

TDD: these tests are written FIRST, implementation follows.
"""


class TestFungalRiskElevated:
    """High humidity + recent rain + warm temps = elevated fungal risk."""

    def test_high_humidity_plus_rain_elevates_fungal_risk(self):
        """Humidity >80% + recent rainfall → fungal risk even if NDVI is borderline."""
        from cultivos.services.crop.disease import assess_disease_weather_risk

        result = assess_disease_weather_risk(
            ndvi_mean=0.45,  # borderline — would be "moderate stress" alone
            stress_pct=35.0,
            thermal_stress_pct=20.0,
            thermal_temp_mean=28.0,
            ndvi_std=0.10,
            humidity_pct=85.0,
            rainfall_mm=15.0,
            temp_c=28.0,
        )

        assert result["risk_level"] in ("alto", "medio")
        assert any("fungic" in r["tipo"].lower() or "hongo" in r["tipo"].lower()
                    for r in result["risks"])

    def test_extreme_humidity_rain_warm_is_alto(self):
        """Very high humidity + heavy rain + warm temp → alto risk."""
        from cultivos.services.crop.disease import assess_disease_weather_risk

        result = assess_disease_weather_risk(
            ndvi_mean=0.50,
            stress_pct=25.0,
            thermal_stress_pct=10.0,
            thermal_temp_mean=30.0,
            ndvi_std=0.10,
            humidity_pct=92.0,
            rainfall_mm=30.0,
            temp_c=30.0,
        )

        assert result["risk_level"] == "alto"


class TestNoFalsePositiveInDry:
    """Dry conditions should NOT trigger fungal risk."""

    def test_low_humidity_no_rain_no_fungal_risk(self):
        """Humidity <60% + no rain → no fungal risk even if temp is warm."""
        from cultivos.services.crop.disease import assess_disease_weather_risk

        result = assess_disease_weather_risk(
            ndvi_mean=0.50,
            stress_pct=25.0,
            thermal_stress_pct=10.0,
            thermal_temp_mean=28.0,
            ndvi_std=0.10,
            humidity_pct=45.0,
            rainfall_mm=0.0,
            temp_c=28.0,
        )

        # Should NOT flag fungal risk
        assert not any("fungic" in r["tipo"].lower() or "hongo" in r["tipo"].lower()
                       for r in result["risks"])

    def test_moderate_humidity_no_rain_no_fungal_risk(self):
        """Humidity 70% but no rain → no fungal risk."""
        from cultivos.services.crop.disease import assess_disease_weather_risk

        result = assess_disease_weather_risk(
            ndvi_mean=0.50,
            stress_pct=25.0,
            thermal_stress_pct=10.0,
            thermal_temp_mean=28.0,
            ndvi_std=0.10,
            humidity_pct=70.0,
            rainfall_mm=0.0,
            temp_c=28.0,
        )

        assert not any("fungic" in r["tipo"].lower() or "hongo" in r["tipo"].lower()
                       for r in result["risks"])


class TestWeatherContextInSpanish:
    """Risk descriptions must include weather context in Spanish."""

    def test_fungal_risk_mentions_humidity_and_rain(self):
        """Fungal risk description includes humidity % and rainfall mm in Spanish."""
        from cultivos.services.crop.disease import assess_disease_weather_risk

        result = assess_disease_weather_risk(
            ndvi_mean=0.42,
            stress_pct=38.0,
            thermal_stress_pct=15.0,
            thermal_temp_mean=29.0,
            ndvi_std=0.10,
            humidity_pct=88.0,
            rainfall_mm=20.0,
            temp_c=29.0,
        )

        fungal_risks = [r for r in result["risks"]
                        if "fungic" in r["tipo"].lower() or "hongo" in r["tipo"].lower()]
        assert len(fungal_risks) > 0
        desc = fungal_risks[0]["descripcion"]
        assert "humedad" in desc.lower()
        assert "lluvia" in desc.lower() or "precipitacion" in desc.lower()
        # All recommendations must be organic
        assert fungal_risks[0]["organico"] is True

    def test_result_includes_weather_summary(self):
        """Result has weather_context field summarizing conditions."""
        from cultivos.services.crop.disease import assess_disease_weather_risk

        result = assess_disease_weather_risk(
            ndvi_mean=0.45,
            stress_pct=35.0,
            thermal_stress_pct=10.0,
            thermal_temp_mean=28.0,
            ndvi_std=0.10,
            humidity_pct=85.0,
            rainfall_mm=12.0,
            temp_c=28.0,
        )

        assert "weather_context" in result
        ctx = result["weather_context"]
        assert "humidity_pct" in ctx
        assert "rainfall_mm" in ctx
        assert "temp_c" in ctx


class TestWeatherFallback:
    """When no weather data, fall back to standard assess_disease_risk behavior."""

    def test_no_weather_defaults_match_base(self):
        """With default weather params, result matches standard risk assessment."""
        from cultivos.services.crop.disease import (
            assess_disease_risk,
            assess_disease_weather_risk,
        )

        base = assess_disease_risk(
            ndvi_mean=0.3,
            stress_pct=65.0,
            thermal_stress_pct=55.0,
            thermal_temp_mean=36.0,
            ndvi_std=0.10,
        )
        weather = assess_disease_weather_risk(
            ndvi_mean=0.3,
            stress_pct=65.0,
            thermal_stress_pct=55.0,
            thermal_temp_mean=36.0,
            ndvi_std=0.10,
            # default weather = benign conditions
        )

        # Base risks should still be present
        assert weather["risk_level"] == base["risk_level"]
        # weather version may have ADDITIONAL risks but should include all base ones
        base_types = {r["tipo"] for r in base["risks"]}
        weather_types = {r["tipo"] for r in weather["risks"]}
        assert base_types.issubset(weather_types)


class TestDiseaseWeatherAPI:
    """API endpoint includes weather data when available."""

    def _seed_farm_with_weather(self, db):
        from cultivos.db.models import Farm, Field, NDVIResult, ThermalResult, WeatherRecord

        farm = Farm(
            name="Rancho Humedo",
            owner_name="Test",
            state="Jalisco",
            location_lat=20.6,
            location_lon=-103.3,
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(
            farm_id=farm.id, name="Parcela Lluviosa", crop_type="maiz", hectares=10
        )
        db.add(field)
        db.commit()
        db.refresh(field)

        # Borderline NDVI — not alarming alone
        ndvi = NDVIResult(
            field_id=field.id,
            ndvi_mean=0.45,
            ndvi_std=0.10,
            ndvi_min=0.2,
            ndvi_max=0.7,
            pixels_total=10000,
            stress_pct=35.0,
            zones=[],
        )
        db.add(ndvi)

        thermal = ThermalResult(
            field_id=field.id,
            temp_mean=28.0,
            temp_std=2.0,
            temp_min=24.0,
            temp_max=34.0,
            pixels_total=10000,
            stress_pct=15.0,
            irrigation_deficit=False,
        )
        db.add(thermal)

        # High humidity + rain weather record
        weather = WeatherRecord(
            farm_id=farm.id,
            temp_c=28.0,
            humidity_pct=88.0,
            wind_kmh=5.0,
            description="Lluvioso",
            rainfall_mm=20.0,
        )
        db.add(weather)
        db.commit()

        return farm.id, field.id

    def test_disease_risk_endpoint_uses_weather(self, client, db):
        """GET /api/farms/{id}/fields/{id}/disease-risk includes weather-based fungal risk."""
        fid, flid = self._seed_farm_with_weather(db)

        resp = client.get(f"/api/farms/{fid}/fields/{flid}/disease-risk")
        assert resp.status_code == 200

        data = resp.json()
        # With high humidity + rain, should detect fungal risk
        assert any("fungic" in r["tipo"].lower() or "hongo" in r["tipo"].lower()
                    for r in data["risks"])
        assert "weather_context" in data
