"""Weather client — fetch current weather and 3-day forecast from OpenWeather API.

Pure HTTP fetch + parse. No database, no side effects beyond the API call.
"""

import httpx


def fetch_weather(lat: float, lon: float, api_key: str | None) -> dict:
    """Fetch current weather and 3-day forecast for given coordinates.

    Returns dict with keys: temp_c, humidity_pct, wind_kmh, description, forecast_3day.
    """
    if not api_key:
        raise ValueError("API key is required — set OPENWEATHER_API_KEY in .env")

    base = "https://api.openweathermap.org/data/2.5"

    # Current weather
    current_resp = httpx.get(
        f"{base}/weather",
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "lang": "es"},
    )
    current_resp.raise_for_status()
    current = current_resp.json()

    # 3-day forecast (5-day API, we take first 3 entries at 24h intervals)
    forecast_resp = httpx.get(
        f"{base}/forecast",
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "lang": "es", "cnt": 3},
    )
    forecast_resp.raise_for_status()
    forecast_data = forecast_resp.json()

    forecast_3day = []
    for entry in forecast_data.get("list", []):
        rain_entry = entry.get("rain", {})
        forecast_rainfall = rain_entry.get("3h", rain_entry.get("1h", 0.0))
        forecast_3day.append({
            "temp_c": entry["main"]["temp"],
            "humidity_pct": entry["main"]["humidity"],
            "wind_kmh": round(entry["wind"]["speed"] * 3.6, 2),
            "description": entry["weather"][0]["description"],
            "rainfall_mm": forecast_rainfall,
        })

    # Current weather: rain.1h or rain.3h (only present when raining)
    rain_data = current.get("rain", {})
    rainfall_mm = rain_data.get("1h", rain_data.get("3h", 0.0))

    return {
        "temp_c": current["main"]["temp"],
        "humidity_pct": current["main"]["humidity"],
        "wind_kmh": round(current["wind"]["speed"] * 3.6, 2),
        "description": current["weather"][0]["description"],
        "rainfall_mm": rainfall_mm,
        "forecast_3day": forecast_3day,
    }
