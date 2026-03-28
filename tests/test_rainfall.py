"""Tests for rainfall tracking in weather records.

Task #4: Add rainfall_mm to WeatherRecord, update weather_client to capture
precipitation from OpenWeather API, fix irrigation to use real rainfall.
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Test 1: WeatherRecord ORM stores rainfall_mm
# ---------------------------------------------------------------------------
class TestWeatherRecordRainfall:
    def test_weather_record_stores_rainfall_mm(self, client, admin_headers):
        """POST /api/farms/{id}/weather with rainfall_mm stores and returns it."""
        farm_resp = client.post("/api/farms", json={
            "name": "Rancho Lluvia",
            "location_lat": 20.6597,
            "location_lon": -103.3496,
        }, headers=admin_headers)
        farm_id = farm_resp.json()["id"]

        post_resp = client.post(f"/api/farms/{farm_id}/weather", json={
            "temp_c": 25.0,
            "humidity_pct": 80.0,
            "wind_kmh": 10.0,
            "description": "lluvia moderada",
            "rainfall_mm": 12.5,
            "forecast_3day": [],
        })
        assert post_resp.status_code == 201
        data = post_resp.json()
        assert data["rainfall_mm"] == 12.5

        # GET returns it too
        get_resp = client.get(f"/api/farms/{farm_id}/weather")
        records = get_resp.json()
        assert records[0]["rainfall_mm"] == 12.5

    def test_weather_record_rainfall_defaults_to_zero(self, client, admin_headers):
        """If rainfall_mm not provided, defaults to 0.0 (backward compat)."""
        farm_resp = client.post("/api/farms", json={
            "name": "Rancho Seco",
            "location_lat": 20.66,
            "location_lon": -103.35,
        }, headers=admin_headers)
        farm_id = farm_resp.json()["id"]

        post_resp = client.post(f"/api/farms/{farm_id}/weather", json={
            "temp_c": 30.0,
            "humidity_pct": 40.0,
            "wind_kmh": 5.0,
            "description": "cielo claro",
            "forecast_3day": [],
        })
        assert post_resp.status_code == 201
        data = post_resp.json()
        assert data["rainfall_mm"] == 0.0


# ---------------------------------------------------------------------------
# Test 2: weather_client captures precipitation from OpenWeather API
# ---------------------------------------------------------------------------
class TestWeatherClientRainfall:
    def test_fetch_weather_captures_rain(self):
        """When OpenWeather returns rain.1h, fetch_weather includes rainfall_mm."""
        from cultivos.services.weather_client import fetch_weather

        mock_current = MagicMock()
        mock_current.json.return_value = {
            "main": {"temp": 22.0, "humidity": 85},
            "wind": {"speed": 3.0},
            "weather": [{"description": "lluvia moderada"}],
            "rain": {"1h": 8.5},
        }

        mock_forecast = MagicMock()
        mock_forecast.json.return_value = {
            "list": [
                {
                    "main": {"temp": 21.0, "humidity": 80},
                    "wind": {"speed": 2.5},
                    "weather": [{"description": "lluvia ligera"}],
                    "rain": {"3h": 4.2},
                },
            ]
        }

        with patch("cultivos.services.weather_client.httpx.get") as mock_get:
            mock_get.side_effect = [mock_current, mock_forecast]
            result = fetch_weather(lat=20.66, lon=-103.35, api_key="test-key")

        assert result["rainfall_mm"] == 8.5
        assert result["forecast_3day"][0]["rainfall_mm"] == 4.2

    def test_fetch_weather_no_rain_returns_zero(self):
        """When OpenWeather has no rain object, rainfall_mm is 0.0."""
        from cultivos.services.weather_client import fetch_weather

        mock_current = MagicMock()
        mock_current.json.return_value = {
            "main": {"temp": 35.0, "humidity": 20},
            "wind": {"speed": 6.0},
            "weather": [{"description": "cielo claro"}],
        }

        mock_forecast = MagicMock()
        mock_forecast.json.return_value = {
            "list": [
                {
                    "main": {"temp": 34.0, "humidity": 25},
                    "wind": {"speed": 5.5},
                    "weather": [{"description": "despejado"}],
                },
            ]
        }

        with patch("cultivos.services.weather_client.httpx.get") as mock_get:
            mock_get.side_effect = [mock_current, mock_forecast]
            result = fetch_weather(lat=20.66, lon=-103.35, api_key="test-key")

        assert result["rainfall_mm"] == 0.0
        assert result["forecast_3day"][0]["rainfall_mm"] == 0.0


# ---------------------------------------------------------------------------
# Test 3: Irrigation schedule uses real rainfall from WeatherRecord
# ---------------------------------------------------------------------------
class TestIrrigationUsesRealRainfall:
    def test_irrigation_uses_stored_rainfall(self, client, admin_headers):
        """When WeatherRecord has rainfall_mm, irrigation schedule reflects it."""
        # Create farm + field
        farm_resp = client.post("/api/farms", json={
            "name": "Rancho Riego",
            "location_lat": 20.66,
            "location_lon": -103.35,
        }, headers=admin_headers)
        farm_id = farm_resp.json()["id"]

        field_resp = client.post(f"/api/farms/{farm_id}/fields", json={
            "name": "Parcela Norte",
            "crop_type": "maiz",
            "hectares": 10.0,
        }, headers=admin_headers)
        field_id = field_resp.json()["id"]

        # Store weather WITH rainfall
        client.post(f"/api/farms/{farm_id}/weather", json={
            "temp_c": 28.0,
            "humidity_pct": 70.0,
            "wind_kmh": 10.0,
            "description": "lluvia reciente",
            "rainfall_mm": 20.0,
            "forecast_3day": [],
        }, headers=admin_headers)

        # Get irrigation schedule — should account for 20mm rainfall
        irrig_resp = client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/irrigation"
        )
        assert irrig_resp.status_code == 200
        data = irrig_resp.json()

        # With 20mm of rain, the recommendation should mention lluvia
        assert "lluvia" in data["recomendacion"].lower() or data["urgencia"] == "baja"

        # Store weather WITHOUT rainfall (dry day)
        client.post(f"/api/farms/{farm_id}/weather", json={
            "temp_c": 38.0,
            "humidity_pct": 20.0,
            "wind_kmh": 15.0,
            "description": "cielo claro",
            "rainfall_mm": 0.0,
            "forecast_3day": [],
        }, headers=admin_headers)

        # Get irrigation again — should be higher urgency
        irrig_resp2 = client.get(
            f"/api/farms/{farm_id}/fields/{field_id}/irrigation"
        )
        data2 = irrig_resp2.json()
        assert data2["urgencia"] == "alta"

        # Water need should be higher when no rain
        assert data2["liters_total_per_ha"] > data["liters_total_per_ha"]
