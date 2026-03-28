"""Tests for the weather forecast card on the field detail page."""

import pytest


@pytest.fixture
def farm_with_weather(client, admin_headers):
    """Create a farm with weather data including 3-day forecast."""
    farm = client.post("/api/farms", json={
        "name": "Rancho Clima",
        "owner_name": "Maria Lopez",
        "location_lat": 20.67,
        "location_lon": -103.35,
        "total_hectares": 30,
        "municipality": "Tlajomulco",
        "state": "Jalisco",
        "country": "MX",
    }, headers=admin_headers).json()
    assert "id" in farm

    client.post(f"/api/farms/{farm['id']}/weather", json={
        "temp_c": 28.5,
        "humidity_pct": 65.0,
        "wind_kmh": 12.3,
        "rainfall_mm": 2.1,
        "description": "Parcialmente nublado",
        "forecast_3day": [
            {"temp_c": 30.0, "humidity_pct": 60.0, "wind_kmh": 10.0,
             "description": "Soleado", "rainfall_mm": 0.0},
            {"temp_c": 27.0, "humidity_pct": 75.0, "wind_kmh": 15.0,
             "description": "Lluvia ligera", "rainfall_mm": 8.5},
            {"temp_c": 29.0, "humidity_pct": 55.0, "wind_kmh": 8.0,
             "description": "Despejado", "rainfall_mm": 0.0},
        ],
    })
    return farm


class TestWeatherForecastCard:
    """Tests for weather forecast card rendering and data."""

    def test_field_html_has_weather_section(self, client):
        """Field detail page includes a weather forecast section."""
        resp = client.get("/campo")
        assert resp.status_code == 200
        html = resp.text
        assert 'id="section-weather"' in html
        assert 'id="weather-content"' in html

    def test_weather_api_returns_forecast(self, client, admin_headers, farm_with_weather):
        """Weather API returns current conditions + 3-day forecast."""
        farm_id = farm_with_weather["id"]
        resp = client.get(f"/api/farms/{farm_id}/weather")
        assert resp.status_code == 200
        records = resp.json()
        assert len(records) >= 1
        latest = records[0]
        assert latest["temp_c"] == 28.5
        assert latest["rainfall_mm"] == 2.1
        assert len(latest["forecast_3day"]) == 3
        # Verify each forecast day has all expected fields
        for day in latest["forecast_3day"]:
            assert "temp_c" in day
            assert "humidity_pct" in day
            assert "wind_kmh" in day
            assert "description" in day
            assert "rainfall_mm" in day

    def test_weather_forecast_rain_detection(self, client, admin_headers, farm_with_weather):
        """Forecast identifies rainy days (rainfall_mm > 0)."""
        farm_id = farm_with_weather["id"]
        resp = client.get(f"/api/farms/{farm_id}/weather")
        records = resp.json()
        forecast = records[0]["forecast_3day"]
        rainy_days = [d for d in forecast if d["rainfall_mm"] > 0]
        assert len(rainy_days) == 1
        assert rainy_days[0]["description"] == "Lluvia ligera"

    def test_weather_empty_records(self, client, admin_headers):
        """Weather card handles farm with no weather records gracefully."""
        farm = client.post("/api/farms", json={
            "name": "Rancho Sin Clima",
            "owner_name": "Pedro",
            "location_lat": 20.5,
            "location_lon": -103.2,
            "total_hectares": 10,
            "municipality": "Zapopan",
            "state": "Jalisco",
            "country": "MX",
        }, headers=admin_headers).json()
        resp = client.get(f"/api/farms/{farm['id']}/weather")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_weather_no_forecast_days(self, client, admin_headers):
        """Weather record with empty forecast_3day is handled."""
        farm = client.post("/api/farms", json={
            "name": "Rancho Basico",
            "owner_name": "Ana",
            "location_lat": 20.6,
            "location_lon": -103.3,
            "total_hectares": 15,
            "municipality": "Guadalajara",
            "state": "Jalisco",
            "country": "MX",
        }, headers=admin_headers).json()
        resp = client.post(f"/api/farms/{farm['id']}/weather", json={
            "temp_c": 25.0,
            "humidity_pct": 50.0,
            "wind_kmh": 5.0,
            "description": "Despejado",
            "rainfall_mm": 0.0,
            "forecast_3day": [],
        })
        assert resp.status_code == 201
        records = client.get(f"/api/farms/{farm['id']}/weather").json()
        assert records[0]["forecast_3day"] == []

    def test_field_js_has_render_weather(self, client):
        """field.js contains a renderWeatherCard function."""
        resp = client.get("/field.js")
        assert resp.status_code == 200
        assert "renderWeatherCard" in resp.text
