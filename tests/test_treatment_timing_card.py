"""Tests for the treatment timing card on the field detail page."""

import pytest
from datetime import datetime
from cultivos.db.models import (
    Farm, Field, TreatmentRecord, WeatherRecord,
)


@pytest.fixture
def farm_with_weather_and_treatments(db):
    """Farm with field, 3-day forecast, and pending treatments."""
    farm = Farm(name="Rancho Timing", state="Jalisco", total_hectares=50)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Maiz", crop_type="maiz", hectares=25)
    db.add(field)
    db.flush()

    # Pending treatments (no applied_at)
    db.add(TreatmentRecord(
        field_id=field.id, health_score_used=65.0,
        problema="Deficiencia de nitrogeno", causa_probable="Suelo agotado",
        tratamiento="Composta de bovino", urgencia="alta",
        prevencion="Rotacion con leguminosas", organic=True,
        costo_estimado_mxn=800,
    ))
    db.add(TreatmentRecord(
        field_id=field.id, health_score_used=70.0,
        problema="Estres hidrico", causa_probable="Sequia",
        tratamiento="Te de composta foliar", urgencia="media",
        prevencion="Mulch", organic=True,
        costo_estimado_mxn=400,
    ))

    # Weather with 3-day forecast
    db.add(WeatherRecord(
        farm_id=farm.id, temp_c=28.0, humidity_pct=65.0,
        wind_kmh=12.0, rainfall_mm=0.0, description="parcialmente nublado",
        forecast_3day=[
            {"temp_c": 30.0, "humidity_pct": 60.0, "wind_kmh": 8.0,
             "description": "soleado", "rainfall_mm": 0.0},
            {"temp_c": 27.0, "humidity_pct": 75.0, "wind_kmh": 5.0,
             "description": "nublado con lluvia ligera", "rainfall_mm": 12.0},
            {"temp_c": 25.0, "humidity_pct": 80.0, "wind_kmh": 6.0,
             "description": "lluvia", "rainfall_mm": 25.0},
        ],
        recorded_at=datetime(2026, 3, 28),
    ))
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


@pytest.fixture
def farm_no_weather(db):
    """Farm with treatments but no weather records."""
    farm = Farm(name="Rancho Sin Clima", state="Jalisco", total_hectares=30)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Frijol", crop_type="frijol", hectares=10)
    db.add(field)
    db.flush()

    db.add(TreatmentRecord(
        field_id=field.id, health_score_used=55.0,
        problema="Plaga", causa_probable="Mosca blanca",
        tratamiento="Extracto de neem", urgencia="alta",
        prevencion="Trampas amarillas", organic=True,
        costo_estimado_mxn=300,
    ))
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


@pytest.fixture
def farm_no_treatments(db):
    """Farm with weather but no treatments."""
    farm = Farm(name="Rancho Sin Trat", state="Jalisco", total_hectares=20)
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Sana", crop_type="aguacate", hectares=15)
    db.add(field)
    db.flush()

    db.add(WeatherRecord(
        farm_id=farm.id, temp_c=22.0, humidity_pct=50.0,
        wind_kmh=10.0, rainfall_mm=0.0, description="despejado",
        forecast_3day=[
            {"temp_c": 24.0, "humidity_pct": 55.0, "wind_kmh": 7.0,
             "description": "soleado", "rainfall_mm": 0.0},
        ],
        recorded_at=datetime(2026, 3, 28),
    ))
    db.commit()
    return {"farm_id": farm.id, "field_id": field.id}


# ── Test: treatment timing endpoint returns timing for each treatment type ──

class TestTreatmentTimingAPI:
    """Test POST /api/intel/treatment-timing returns valid timing data."""

    def test_timing_organic_amendment(self, client):
        """Organic amendment timing with rain in forecast."""
        resp = client.post("/api/intel/treatment-timing", json={
            "treatment_type": "organic_amendment",
            "forecast_3day": [
                {"description": "soleado", "temp_c": 30.0, "humidity_pct": 60.0, "wind_kmh": 8.0},
                {"description": "lluvia ligera", "temp_c": 27.0, "humidity_pct": 75.0, "wind_kmh": 5.0},
                {"description": "lluvia", "temp_c": 25.0, "humidity_pct": 80.0, "wind_kmh": 6.0},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "best_day" in data
        assert "best_time" in data
        assert "reason" in data
        assert "avoid_days" in data
        assert isinstance(data["best_day"], int)
        assert 0 <= data["best_day"] <= 2

    def test_timing_foliar_spray(self, client):
        """Foliar spray timing — avoids rainy days."""
        resp = client.post("/api/intel/treatment-timing", json={
            "treatment_type": "foliar_spray",
            "forecast_3day": [
                {"description": "soleado", "temp_c": 30.0, "humidity_pct": 60.0, "wind_kmh": 8.0},
                {"description": "lluvia", "temp_c": 27.0, "humidity_pct": 75.0, "wind_kmh": 5.0},
                {"description": "lluvia fuerte", "temp_c": 25.0, "humidity_pct": 80.0, "wind_kmh": 6.0},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["best_day"] == 0  # day 0 is dry — best for foliar

    def test_timing_soil_drench(self, client):
        """Soil drench timing."""
        resp = client.post("/api/intel/treatment-timing", json={
            "treatment_type": "soil_drench",
            "forecast_3day": [
                {"description": "soleado", "temp_c": 28.0, "humidity_pct": 55.0, "wind_kmh": 10.0},
                {"description": "nublado", "temp_c": 26.0, "humidity_pct": 65.0, "wind_kmh": 8.0},
                {"description": "soleado", "temp_c": 29.0, "humidity_pct": 50.0, "wind_kmh": 12.0},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "best_day" in data
        assert "best_time" in data

    def test_timing_empty_forecast(self, client):
        """Empty forecast returns safe default."""
        resp = client.post("/api/intel/treatment-timing", json={
            "treatment_type": "organic_amendment",
            "forecast_3day": [],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["best_day"] == 0
        assert "mañana" in data["best_time"].lower()


# ── Test: weather endpoint returns forecast data for card ──

class TestWeatherForecastForTiming:
    """Test that weather endpoint returns forecast_3day needed by timing card."""

    def test_weather_has_forecast(self, client, farm_with_weather_and_treatments):
        fid = farm_with_weather_and_treatments["farm_id"]
        resp = client.get(f"/api/farms/{fid}/weather")
        assert resp.status_code == 200
        records = resp.json()
        assert len(records) > 0
        assert "forecast_3day" in records[0]
        assert len(records[0]["forecast_3day"]) == 3

    def test_weather_forecast_fields(self, client, farm_with_weather_and_treatments):
        fid = farm_with_weather_and_treatments["farm_id"]
        resp = client.get(f"/api/farms/{fid}/weather")
        day = resp.json()[0]["forecast_3day"][0]
        assert "temp_c" in day
        assert "humidity_pct" in day
        assert "wind_kmh" in day
        assert "description" in day


# ── Test: pending treatments available for timing ──

class TestPendingTreatments:
    """Verify treatments endpoint returns pending treatments for timing card."""

    def test_pending_treatments_returned(self, client, farm_with_weather_and_treatments):
        ids = farm_with_weather_and_treatments
        resp = client.get(f"/api/farms/{ids['farm_id']}/fields/{ids['field_id']}/treatments")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Pending = no applied_at
        assert all(t["applied_at"] is None for t in data)

    def test_no_treatments_returns_empty(self, client, farm_no_treatments):
        ids = farm_no_treatments
        resp = client.get(f"/api/farms/{ids['farm_id']}/fields/{ids['field_id']}/treatments")
        assert resp.status_code == 200
        assert resp.json() == []
