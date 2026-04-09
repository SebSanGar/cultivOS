"""Tests for weather alert detection — service + API + frontend."""

import pytest

from cultivos.services.intelligence.weather_alerts import (
    EXTREME_HEAT_C,
    FROST_TEMP_C,
    HEAVY_RAIN_MM,
    HIGH_WIND_KMH,
    detect_weather_alerts,
)


# ── Pure service tests ──


class TestFrostDetection:
    def test_frost_below_zero_is_critical(self):
        alerts = detect_weather_alerts(temp_c=-2.0, humidity_pct=80, wind_kmh=10, rainfall_mm=0)
        frost = [a for a in alerts if a["alert_type"] == "frost"]
        assert len(frost) == 1
        assert frost[0]["severity"] == "critica"
        assert "-2.0" in frost[0]["message"]
        assert len(frost[0]["actions"]) >= 3

    def test_frost_near_zero_is_moderate(self):
        alerts = detect_weather_alerts(temp_c=1.5, humidity_pct=80, wind_kmh=10, rainfall_mm=0)
        frost = [a for a in alerts if a["alert_type"] == "frost"]
        assert len(frost) == 1
        assert frost[0]["severity"] == "moderada"

    def test_no_frost_at_safe_temp(self):
        alerts = detect_weather_alerts(temp_c=15.0, humidity_pct=60, wind_kmh=10, rainfall_mm=0)
        frost = [a for a in alerts if a["alert_type"] == "frost"]
        assert len(frost) == 0

    def test_frost_at_boundary(self):
        alerts = detect_weather_alerts(temp_c=FROST_TEMP_C, humidity_pct=80, wind_kmh=10, rainfall_mm=0)
        frost = [a for a in alerts if a["alert_type"] == "frost"]
        assert len(frost) == 1


class TestExtremeHeatDetection:
    def test_extreme_heat_above_42_is_critical(self):
        alerts = detect_weather_alerts(temp_c=43.0, humidity_pct=20, wind_kmh=5, rainfall_mm=0)
        heat = [a for a in alerts if a["alert_type"] == "extreme_heat"]
        assert len(heat) == 1
        assert heat[0]["severity"] == "critica"

    def test_extreme_heat_moderate(self):
        alerts = detect_weather_alerts(temp_c=39.0, humidity_pct=25, wind_kmh=5, rainfall_mm=0)
        heat = [a for a in alerts if a["alert_type"] == "extreme_heat"]
        assert len(heat) == 1
        assert heat[0]["severity"] == "moderada"

    def test_no_heat_alert_at_normal_temp(self):
        alerts = detect_weather_alerts(temp_c=30.0, humidity_pct=50, wind_kmh=10, rainfall_mm=5)
        heat = [a for a in alerts if a["alert_type"] == "extreme_heat"]
        assert len(heat) == 0


class TestHeavyRainDetection:
    def test_heavy_rain_critical(self):
        alerts = detect_weather_alerts(temp_c=20, humidity_pct=95, wind_kmh=15, rainfall_mm=85.0)
        rain = [a for a in alerts if a["alert_type"] == "heavy_rain"]
        assert len(rain) == 1
        assert rain[0]["severity"] == "critica"

    def test_heavy_rain_moderate(self):
        alerts = detect_weather_alerts(temp_c=20, humidity_pct=90, wind_kmh=10, rainfall_mm=55.0)
        rain = [a for a in alerts if a["alert_type"] == "heavy_rain"]
        assert len(rain) == 1
        assert rain[0]["severity"] == "moderada"

    def test_no_rain_alert_below_threshold(self):
        alerts = detect_weather_alerts(temp_c=20, humidity_pct=70, wind_kmh=10, rainfall_mm=30.0)
        rain = [a for a in alerts if a["alert_type"] == "heavy_rain"]
        assert len(rain) == 0


class TestHighWindDetection:
    def test_high_wind_critical(self):
        alerts = detect_weather_alerts(temp_c=20, humidity_pct=50, wind_kmh=85.0, rainfall_mm=0)
        wind = [a for a in alerts if a["alert_type"] == "high_wind"]
        assert len(wind) == 1
        assert wind[0]["severity"] == "critica"

    def test_high_wind_moderate(self):
        alerts = detect_weather_alerts(temp_c=20, humidity_pct=50, wind_kmh=65.0, rainfall_mm=0)
        wind = [a for a in alerts if a["alert_type"] == "high_wind"]
        assert len(wind) == 1
        assert wind[0]["severity"] == "moderada"

    def test_no_wind_alert_below_threshold(self):
        alerts = detect_weather_alerts(temp_c=20, humidity_pct=50, wind_kmh=40.0, rainfall_mm=0)
        wind = [a for a in alerts if a["alert_type"] == "high_wind"]
        assert len(wind) == 0


class TestHailDetection:
    def test_hail_from_description(self):
        alerts = detect_weather_alerts(
            temp_c=15, humidity_pct=80, wind_kmh=30, rainfall_mm=20,
            description="Tormenta con granizo",
        )
        hail = [a for a in alerts if a["alert_type"] == "hail"]
        assert len(hail) == 1
        assert hail[0]["severity"] == "critica"

    def test_hail_english_keyword(self):
        alerts = detect_weather_alerts(
            temp_c=15, humidity_pct=80, wind_kmh=30, rainfall_mm=20,
            description="thunderstorm with hail",
        )
        hail = [a for a in alerts if a["alert_type"] == "hail"]
        assert len(hail) == 1

    def test_no_hail_normal_description(self):
        alerts = detect_weather_alerts(
            temp_c=20, humidity_pct=60, wind_kmh=10, rainfall_mm=5,
            description="parcialmente nublado",
        )
        hail = [a for a in alerts if a["alert_type"] == "hail"]
        assert len(hail) == 0


class TestForecastAlerts:
    def test_forecast_frost_detected(self):
        alerts = detect_weather_alerts(
            temp_c=15, humidity_pct=50, wind_kmh=10, rainfall_mm=0,
            forecast_3day=[
                {"temp_c": 12.0, "humidity_pct": 60, "wind_kmh": 5, "rainfall_mm": 0, "description": "despejado"},
                {"temp_c": -1.0, "humidity_pct": 85, "wind_kmh": 3, "rainfall_mm": 0, "description": "despejado"},
                {"temp_c": 8.0, "humidity_pct": 55, "wind_kmh": 10, "rainfall_mm": 0, "description": "nublado"},
            ],
        )
        frost = [a for a in alerts if a["alert_type"] == "frost"]
        assert len(frost) == 1
        assert frost[0]["source"] == "forecast_day_2"

    def test_multiple_alert_types_combined(self):
        alerts = detect_weather_alerts(
            temp_c=-3.0, humidity_pct=90, wind_kmh=70, rainfall_mm=60,
            description="tormenta con granizo",
        )
        types = {a["alert_type"] for a in alerts}
        assert "frost" in types
        assert "high_wind" in types
        assert "heavy_rain" in types
        assert "hail" in types

    def test_no_alerts_normal_weather(self):
        alerts = detect_weather_alerts(
            temp_c=22.0, humidity_pct=55, wind_kmh=15, rainfall_mm=5,
            description="soleado",
            forecast_3day=[
                {"temp_c": 24, "humidity_pct": 50, "wind_kmh": 10, "rainfall_mm": 2, "description": "despejado"},
            ],
        )
        assert alerts == []

    def test_source_field_tracks_origin(self):
        alerts = detect_weather_alerts(
            temp_c=40.0, humidity_pct=20, wind_kmh=5, rainfall_mm=0,
            forecast_3day=[
                {"temp_c": 41.0, "humidity_pct": 18, "wind_kmh": 5, "rainfall_mm": 0, "description": ""},
            ],
        )
        sources = {a["source"] for a in alerts}
        assert "current" in sources
        assert "forecast_day_1" in sources


class TestAlertActions:
    def test_all_alerts_have_actions(self):
        alerts = detect_weather_alerts(
            temp_c=-3.0, humidity_pct=90, wind_kmh=70, rainfall_mm=60,
            description="granizo",
        )
        for alert in alerts:
            assert len(alert["actions"]) >= 3
            assert all(isinstance(a, str) for a in alert["actions"])

    def test_actions_are_in_spanish(self):
        alerts = detect_weather_alerts(temp_c=-2.0, humidity_pct=80, wind_kmh=10, rainfall_mm=0)
        frost = [a for a in alerts if a["alert_type"] == "frost"][0]
        assert any("cultivo" in action.lower() for action in frost["actions"])


# ── API endpoint tests ──


class TestWeatherAlertsEndpoint:
    def _seed_farm_and_weather(self, db, temp_c=20.0, rainfall_mm=5.0, wind_kmh=10.0, description="soleado", forecast_3day=None):
        from cultivos.db.models import Farm, WeatherRecord
        farm = Farm(name="Test Farm", state="Jalisco", total_hectares=50)
        db.add(farm)
        db.flush()
        wr = WeatherRecord(
            farm_id=farm.id,
            temp_c=temp_c,
            humidity_pct=60.0,
            wind_kmh=wind_kmh,
            rainfall_mm=rainfall_mm,
            description=description,
            forecast_3day=forecast_3day or [],
        )
        db.add(wr)
        db.commit()
        return farm.id

    def test_no_alerts_normal_weather(self, client, db):
        farm_id = self._seed_farm_and_weather(db)
        resp = client.get(f"/api/farms/{farm_id}/weather/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["farm_id"] == farm_id
        assert data["alerts"] == []
        assert data["weather_record_id"] is not None

    def test_frost_alert_returned(self, client, db):
        farm_id = self._seed_farm_and_weather(db, temp_c=-1.0)
        resp = client.get(f"/api/farms/{farm_id}/weather/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts"]) >= 1
        types = {a["alert_type"] for a in data["alerts"]}
        assert "frost" in types

    def test_forecast_alerts_included(self, client, db):
        forecast = [
            {"temp_c": 10, "humidity_pct": 50, "wind_kmh": 5, "rainfall_mm": 0, "description": ""},
            {"temp_c": 0.5, "humidity_pct": 90, "wind_kmh": 3, "rainfall_mm": 0, "description": ""},
        ]
        farm_id = self._seed_farm_and_weather(db, forecast_3day=forecast)
        resp = client.get(f"/api/farms/{farm_id}/weather/alerts")
        data = resp.json()
        frost = [a for a in data["alerts"] if a["alert_type"] == "frost"]
        assert len(frost) >= 1

    def test_404_for_missing_farm(self, client, db):
        resp = client.get("/api/farms/9999/weather/alerts")
        assert resp.status_code == 404

    def test_empty_alerts_when_no_weather_records(self, client, db):
        from cultivos.db.models import Farm
        farm = Farm(name="Empty Farm", state="Jalisco", total_hectares=10)
        db.add(farm)
        db.commit()
        resp = client.get(f"/api/farms/{farm.id}/weather/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["alerts"] == []
        assert data["weather_record_id"] is None


# ── Frontend page tests ──


class TestClimaPageWeatherAlerts:
    def test_clima_page_loads(self, client):
        resp = client.get("/clima")
        assert resp.status_code == 200
        assert b"Panel Climatico" in resp.content

    def test_clima_page_has_alerts_section(self, client):
        resp = client.get("/clima")
        assert b"clima-weather-alerts" in resp.content

    def test_clima_page_has_alerts_title(self, client):
        resp = client.get("/clima")
        assert b"Alertas Climaticas" in resp.content
