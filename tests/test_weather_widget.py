"""Tests for the dashboard weather widget."""

import pytest


@pytest.fixture
def farm_with_weather(client, admin_headers):
    """Create a farm with weather data for widget testing."""
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

    # Add weather record with 3-day forecast
    resp = client.post(f"/api/farms/{farm['id']}/weather", json={
        "temp_c": 28.5,
        "humidity_pct": 65.0,
        "wind_kmh": 12.3,
        "description": "Parcialmente nublado",
        "forecast_3day": [
            {"temp_c": 30.0, "humidity_pct": 60.0, "wind_kmh": 10.0, "description": "Soleado"},
            {"temp_c": 27.0, "humidity_pct": 75.0, "wind_kmh": 15.0, "description": "Lluvia ligera"},
            {"temp_c": 29.0, "humidity_pct": 55.0, "wind_kmh": 8.0, "description": "Despejado"},
        ],
    })
    assert resp.status_code == 201

    return farm


def test_weather_widget_html(client):
    """Dashboard HTML includes a weather widget section."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "weather-widget" in html


def test_weather_data_displayed(client, admin_headers, farm_with_weather):
    """Weather API returns temp, humidity, wind for the dashboard to display."""
    farm_id = farm_with_weather["id"]
    resp = client.get(f"/api/farms/{farm_id}/weather")
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) >= 1
    latest = records[0]
    assert latest["temp_c"] == 28.5
    assert latest["humidity_pct"] == 65.0
    assert latest["wind_kmh"] == 12.3
    assert latest["description"] == "Parcialmente nublado"


def test_forecast_days(client, admin_headers, farm_with_weather):
    """Weather record includes 3-day forecast with descriptions."""
    farm_id = farm_with_weather["id"]
    resp = client.get(f"/api/farms/{farm_id}/weather")
    records = resp.json()
    forecast = records[0]["forecast_3day"]
    assert len(forecast) == 3
    assert forecast[0]["description"] == "Soleado"
    assert forecast[1]["description"] == "Lluvia ligera"
    assert forecast[2]["description"] == "Despejado"
