"""Weather seed must emit the canonical ForecastDay shape.

Older seeds wrote forecast_3day entries as {day, temp_c, rain_mm}; the API's
ForecastDay model requires temp_c/humidity_pct/wind_kmh/description/rainfall_mm,
so GET /api/farms/{id}/weather 500'd on every seeded DB (found by the EN crawl
audit — weather widget failed silently on /campo and /clima).
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import scripts.seed_demo as sd
from cultivos.app import create_app
from cultivos.db.models import Farm, WeatherRecord
from cultivos.db.session import get_db

CANONICAL_KEYS = {"temp_c", "humidity_pct", "wind_kmh", "description", "rainfall_mm"}


@pytest.fixture()
def farm_with_weather(db):
    farm = Farm(name="Weather Farm [DEMO]", owner_name="Test", location_lat=20.0,
                location_lon=-103.0, municipality="Zapopan", total_hectares=10)
    db.add(farm)
    db.commit()
    now = datetime.utcnow()
    sd._seed_weather_history(db, farm, now, now - timedelta(days=30))
    db.commit()
    return farm


@pytest.fixture()
def client(db):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    with TestClient(application, raise_server_exceptions=False) as c:
        yield c
    application.dependency_overrides.clear()


class TestSeedShape:
    def test_forecast_entries_are_canonical(self, db, farm_with_weather):
        recs = db.query(WeatherRecord).all()
        assert recs
        for rec in recs:
            for entry in rec.forecast_3day:
                assert CANONICAL_KEYS <= set(entry), entry

    def test_descriptions_are_english(self, db, farm_with_weather):
        descs = {r.description for r in db.query(WeatherRecord).all()}
        assert not (descs & set(sd._WEATHER_DESC_EN)), descs

    def test_weather_endpoint_returns_200(self, client, db, farm_with_weather):
        resp = client.get(f"/api/farms/{farm_with_weather.id}/weather")
        assert resp.status_code == 200
        body = resp.json()
        records = body["data"] if isinstance(body, dict) else body
        assert records and CANONICAL_KEYS <= set(records[0]["forecast_3day"][0])


class TestHeal:
    def test_heals_legacy_rows_and_is_idempotent(self, client, db, farm_with_weather):
        for rec in db.query(WeatherRecord).all():
            rec.description = "Lluvia temporal"
            rec.forecast_3day = [
                {"day": 1, "temp_c": 28.0, "rain_mm": 2.0},
                {"day": 2, "temp_c": 29.0, "rain_mm": 7.0},
            ]
        db.commit()

        resp = client.get(f"/api/farms/{farm_with_weather.id}/weather")
        assert resp.status_code == 500  # legacy shape really breaks the API

        assert sd._heal_weather_forecast(db) > 0
        db.expire_all()
        rec = db.query(WeatherRecord).first()
        assert rec.description == "Seasonal rain"
        assert all(CANONICAL_KEYS <= set(e) for e in rec.forecast_3day)

        resp = client.get(f"/api/farms/{farm_with_weather.id}/weather")
        assert resp.status_code == 200

        assert sd._heal_weather_forecast(db) == 0
