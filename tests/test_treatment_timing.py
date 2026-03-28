"""Tests for treatment timing optimizer — TDD first.

Pure function: treatment_type + 3-day forecast → optimal application window.
"""

import pytest
from cultivos.services.intelligence.recommendations import (
    optimize_treatment_timing,
    ForecastInput,
)
from fastapi.testclient import TestClient
from cultivos.app import create_app


# ── Fixtures ───────────────────────────────────────────────────────────

def _forecast(descriptions: list[str], temps: list[float] | None = None,
              winds: list[float] | None = None, humidities: list[float] | None = None) -> list[ForecastInput]:
    """Build a 3-day forecast from descriptions and optional overrides."""
    temps = temps or [28.0, 28.0, 28.0]
    winds = winds or [8.0, 8.0, 8.0]
    humidities = humidities or [55.0, 55.0, 55.0]
    return [
        ForecastInput(description=d, temp_c=t, wind_kmh=w, humidity_pct=h)
        for d, t, w, h in zip(descriptions, temps, winds, humidities)
    ]


# ── Organic amendment recommends pre-rain timing ──────────────────────

class TestOrganicAmendmentTiming:
    def test_amendment_prefers_day_before_rain(self):
        """Organic amendment (composta, abono) should be applied before rain
        so moisture helps incorporation."""
        forecast = _forecast(["soleado", "lluvia ligera", "nublado"])
        result = optimize_treatment_timing("organic_amendment", forecast)
        assert result["best_day"] == 0  # apply day 0, rain comes day 1
        assert "lluvia" in result["reason"].lower()

    def test_amendment_same_day_rain_still_ok(self):
        """If rain is day 0, amendment can go same day (rain helps)."""
        forecast = _forecast(["lluvia ligera", "soleado", "soleado"])
        result = optimize_treatment_timing("organic_amendment", forecast)
        assert result["best_day"] == 0  # rain day is fine for amendments

    def test_amendment_no_rain_picks_coolest_day(self):
        """No rain in forecast → pick the coolest day for amendment."""
        forecast = _forecast(
            ["soleado", "soleado", "nublado"],
            temps=[35.0, 30.0, 28.0],
        )
        result = optimize_treatment_timing("organic_amendment", forecast)
        assert result["best_day"] == 2  # coolest day


# ── Foliar spray avoids rain day ──────────────────────────────────────

class TestFoliarSprayTiming:
    def test_foliar_avoids_rain_day(self):
        """Foliar spray must NOT be applied on a rain day — gets washed off."""
        forecast = _forecast(["lluvia", "soleado", "soleado"])
        result = optimize_treatment_timing("foliar_spray", forecast)
        assert result["best_day"] != 0  # avoid the rain day
        assert 0 in result["avoid_days"]

    def test_foliar_avoids_high_wind(self):
        """Foliar spray should avoid days with wind > 20 km/h (drift)."""
        forecast = _forecast(
            ["soleado", "soleado", "soleado"],
            winds=[25.0, 10.0, 8.0],
        )
        result = optimize_treatment_timing("foliar_spray", forecast)
        assert result["best_day"] != 0  # avoid windy day
        assert 0 in result["avoid_days"]

    def test_foliar_prefers_early_morning(self):
        """Foliar spray recommends early morning application."""
        forecast = _forecast(["soleado", "soleado", "soleado"])
        result = optimize_treatment_timing("foliar_spray", forecast)
        assert "mañana" in result["best_time"].lower() or "am" in result["best_time"].lower()

    def test_foliar_all_rain_picks_least_rain(self):
        """If all days have rain, pick the one with lightest rain description."""
        forecast = _forecast(["tormenta fuerte", "lluvia ligera", "lluvia moderada"])
        result = optimize_treatment_timing("foliar_spray", forecast)
        assert result["best_day"] == 1  # lightest rain


# ── Timing changes with different forecasts ───────────────────────────

class TestTimingChangesWithForecast:
    def test_different_rain_pattern_changes_amendment_day(self):
        """Rain on day 2 instead of day 1 → amendment moves to day 1."""
        forecast_rain_day1 = _forecast(["soleado", "lluvia", "soleado"])
        forecast_rain_day2 = _forecast(["soleado", "soleado", "lluvia"])

        result1 = optimize_treatment_timing("organic_amendment", forecast_rain_day1)
        result2 = optimize_treatment_timing("organic_amendment", forecast_rain_day2)

        assert result1["best_day"] == 0  # apply before day-1 rain
        assert result2["best_day"] == 1  # apply before day-2 rain

    def test_extreme_heat_recommends_early_morning(self):
        """Temps >= 38C → recommend early morning (6-8 AM)."""
        forecast = _forecast(
            ["soleado", "soleado", "soleado"],
            temps=[40.0, 38.0, 32.0],
        )
        result = optimize_treatment_timing("organic_amendment", forecast)
        assert "6" in result["best_time"] or "temprano" in result["best_time"].lower()

    def test_returns_all_required_fields(self):
        """Result must have: best_day, best_time, reason, avoid_days."""
        forecast = _forecast(["soleado", "soleado", "soleado"])
        result = optimize_treatment_timing("foliar_spray", forecast)
        assert "best_day" in result
        assert "best_time" in result
        assert "reason" in result
        assert "avoid_days" in result
        assert isinstance(result["best_day"], int)
        assert isinstance(result["avoid_days"], list)

    def test_empty_forecast_returns_day_zero(self):
        """No forecast data → default to day 0 with generic advice."""
        result = optimize_treatment_timing("foliar_spray", [])
        assert result["best_day"] == 0

    def test_soil_drench_avoids_saturated_soil(self):
        """Soil drench should avoid day right after heavy rain (saturated)."""
        forecast = _forecast(
            ["tormenta fuerte", "nublado", "soleado"],
            humidities=[95.0, 80.0, 60.0],
        )
        result = optimize_treatment_timing("soil_drench", forecast)
        assert result["best_day"] == 2  # wait for soil to dry


# ── API route tests ───────────────────────────────────────────────────

class TestTimingAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = TestClient(create_app())

    def test_post_treatment_timing_returns_200(self):
        resp = self.client.post("/api/intel/treatment-timing", json={
            "treatment_type": "foliar_spray",
            "forecast_3day": [
                {"description": "soleado", "temp_c": 28, "humidity_pct": 55, "wind_kmh": 8},
                {"description": "lluvia", "temp_c": 25, "humidity_pct": 80, "wind_kmh": 5},
                {"description": "soleado", "temp_c": 30, "humidity_pct": 50, "wind_kmh": 10},
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["best_day"] == 0
        assert 1 in data["avoid_days"]

    def test_post_treatment_timing_amendment(self):
        resp = self.client.post("/api/intel/treatment-timing", json={
            "treatment_type": "organic_amendment",
            "forecast_3day": [
                {"description": "soleado"},
                {"description": "lluvia ligera"},
                {"description": "nublado"},
            ]
        })
        assert resp.status_code == 200
        assert resp.json()["best_day"] == 0

    def test_post_empty_forecast(self):
        resp = self.client.post("/api/intel/treatment-timing", json={
            "treatment_type": "foliar_spray",
            "forecast_3day": [],
        })
        assert resp.status_code == 200
        assert resp.json()["best_day"] == 0
