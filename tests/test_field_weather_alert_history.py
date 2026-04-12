"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/weather-alert-history (#209).

Aggregates severe-weather alerts (computed from WeatherRecord rows via the
existing detect_weather_alerts pure function) over a window. Returns per-type
counts, dominant severity, most-frequent type, alerts/month average, and
first-half vs second-half trend.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, WeatherRecord


def _make_farm(db, name="Rancho Alertas"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Parcela Alertas", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_weather(
    db,
    farm_id,
    *,
    days_ago: int,
    temp=22.0,
    humidity=55.0,
    wind=10.0,
    rain=0.0,
    description="",
):
    w = WeatherRecord(
        farm_id=farm_id,
        temp_c=temp,
        humidity_pct=humidity,
        wind_kmh=wind,
        rainfall_mm=rain,
        description=description,
        forecast_3day=[],
        recorded_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(w)
    db.commit()
    return w


def test_weather_alert_history_404_farm(client):
    r = client.get("/api/farms/9999/fields/1/weather-alert-history")
    assert r.status_code == 404


def test_weather_alert_history_404_field(client, db):
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/9999/weather-alert-history")
    assert r.status_code == 404


def test_weather_alert_history_empty(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/weather-alert-history?days=90"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["field_id"] == field.id
    assert body["period_days"] == 90
    assert body["total_alerts"] == 0
    assert body["by_type"] == []
    assert body["most_frequent_type"] is None
    assert body["alerts_per_month_avg"] == 0.0
    assert body["trend"] == "stable"


def test_weather_alert_history_basic(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # 1 frost, 1 extreme_heat, 1 heavy_rain across the window
    _add_weather(db, farm.id, days_ago=10, temp=1.0)  # frost (critica @ <=2)
    _add_weather(db, farm.id, days_ago=20, temp=39.0)  # extreme_heat
    _add_weather(db, farm.id, days_ago=30, rain=80.0)  # heavy_rain
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/weather-alert-history?days=90"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_alerts"] == 3
    types = {row["alert_type"] for row in body["by_type"]}
    assert "frost" in types
    assert "extreme_heat" in types
    assert "heavy_rain" in types
    for row in body["by_type"]:
        assert row["count"] == 1
        assert row["last_alert_at"] is not None
        assert row["dominant_severity"] in ("critica", "moderada")


def test_weather_alert_history_most_frequent(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # 3 frost rows + 1 heavy_rain → frost is most frequent
    _add_weather(db, farm.id, days_ago=5, temp=0.5)
    _add_weather(db, farm.id, days_ago=15, temp=1.0)
    _add_weather(db, farm.id, days_ago=25, temp=1.5)
    _add_weather(db, farm.id, days_ago=35, rain=70.0)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/weather-alert-history?days=90"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_alerts"] == 4
    assert body["most_frequent_type"] == "frost"
    # alerts_per_month_avg = 4 / (90/30) = 1.333...
    assert abs(body["alerts_per_month_avg"] - (4 / 3)) < 0.01


def test_weather_alert_history_trend_rising(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # 90-day window: first half = days 46-90 (older), second half = days 0-45 (newer)
    # 1 alert in first half, 4 alerts in second half → rising
    _add_weather(db, farm.id, days_ago=80, temp=1.0)  # frost, first half
    _add_weather(db, farm.id, days_ago=10, temp=1.0)  # frost, second half
    _add_weather(db, farm.id, days_ago=15, temp=1.0)  # frost, second half
    _add_weather(db, farm.id, days_ago=20, temp=1.0)  # frost, second half
    _add_weather(db, farm.id, days_ago=25, temp=1.0)  # frost, second half
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/weather-alert-history?days=90"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_alerts"] == 5
    assert body["trend"] == "rising"
