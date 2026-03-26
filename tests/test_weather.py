"""Tests for Weather service — fetch, store, and retrieve weather data for farms."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ---------------------------------------------------------------------------
# Test 1: fetch_weather returns temp, humidity, wind, description, forecast_3day
# ---------------------------------------------------------------------------
class TestFetchWeather:
    def test_fetch_weather_returns_temp_humidity_wind(self):
        """Mock HTTP call to OpenWeather, assert response has all required fields."""
        from cultivos.services.weather_client import fetch_weather

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 28.5, "humidity": 65},
            "wind": {"speed": 4.2},  # m/s
            "weather": [{"description": "cielo claro"}],
        }

        mock_forecast_response = MagicMock()
        mock_forecast_response.status_code = 200
        mock_forecast_response.json.return_value = {
            "list": [
                {
                    "dt": 1711900800,
                    "main": {"temp": 27.0, "humidity": 60},
                    "wind": {"speed": 3.5},
                    "weather": [{"description": "nubes dispersas"}],
                },
                {
                    "dt": 1711987200,
                    "main": {"temp": 29.0, "humidity": 55},
                    "wind": {"speed": 5.0},
                    "weather": [{"description": "lluvia ligera"}],
                },
                {
                    "dt": 1712073600,
                    "main": {"temp": 26.0, "humidity": 70},
                    "wind": {"speed": 2.8},
                    "weather": [{"description": "nublado"}],
                },
            ]
        }

        with patch("cultivos.services.weather_client.httpx.get") as mock_get:
            mock_get.side_effect = [mock_response, mock_forecast_response]
            result = fetch_weather(lat=20.6597, lon=-103.3496, api_key="test-key")

        assert "temp_c" in result
        assert "humidity_pct" in result
        assert "wind_kmh" in result
        assert "description" in result
        assert "forecast_3day" in result

        assert result["temp_c"] == 28.5
        assert result["humidity_pct"] == 65
        # wind: 4.2 m/s * 3.6 = 15.12 km/h
        assert abs(result["wind_kmh"] - 15.12) < 0.1
        assert result["description"] == "cielo claro"
        assert len(result["forecast_3day"]) == 3

    def test_fetch_weather_missing_api_key_raises(self):
        """No OPENWEATHER_API_KEY → raises clear error."""
        from cultivos.services.weather_client import fetch_weather

        with pytest.raises(ValueError, match="API key"):
            fetch_weather(lat=20.6597, lon=-103.3496, api_key=None)


# ---------------------------------------------------------------------------
# Test 3 & 4: WeatherRecord CRUD via API
# ---------------------------------------------------------------------------
class TestWeatherAPI:
    def _create_farm_and_field(self, client, admin_headers):
        """Helper — create a farm with coordinates for weather lookup."""
        farm_resp = client.post("/api/farms", json={
            "name": "Rancho Prueba",
            "location_lat": 20.6597,
            "location_lon": -103.3496,
        }, headers=admin_headers)
        assert farm_resp.status_code == 201
        return farm_resp.json()

    def test_weather_record_crud(self, client, admin_headers):
        """POST /api/farms/{id}/weather stores a WeatherRecord, GET returns it."""
        farm = self._create_farm_and_field(client, admin_headers)
        farm_id = farm["id"]

        # POST weather record
        post_resp = client.post(f"/api/farms/{farm_id}/weather", json={
            "temp_c": 28.5,
            "humidity_pct": 65,
            "wind_kmh": 15.12,
            "description": "cielo claro",
            "forecast_3day": [
                {"temp_c": 27.0, "humidity_pct": 60, "wind_kmh": 12.6, "description": "nubes dispersas"},
                {"temp_c": 29.0, "humidity_pct": 55, "wind_kmh": 18.0, "description": "lluvia ligera"},
                {"temp_c": 26.0, "humidity_pct": 70, "wind_kmh": 10.1, "description": "nublado"},
            ],
        })
        assert post_resp.status_code == 201
        data = post_resp.json()
        assert data["temp_c"] == 28.5
        assert data["humidity_pct"] == 65
        assert data["wind_kmh"] == 15.12
        assert data["description"] == "cielo claro"
        assert len(data["forecast_3day"]) == 3

        # GET weather records
        get_resp = client.get(f"/api/farms/{farm_id}/weather")
        assert get_resp.status_code == 200
        records = get_resp.json()
        assert len(records) == 1
        assert records[0]["temp_c"] == 28.5

    def test_weather_record_links_to_farm(self, client):
        """WeatherRecord.farm_id FK works, 404 if farm not found."""
        # Try to POST weather for non-existent farm
        resp = client.post("/api/farms/9999/weather", json={
            "temp_c": 28.5,
            "humidity_pct": 65,
            "wind_kmh": 15.12,
            "description": "cielo claro",
            "forecast_3day": [],
        })
        assert resp.status_code == 404
