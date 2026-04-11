"""Tests for water use efficiency report.

GET /api/farms/{farm_id}/fields/{field_id}/water-efficiency
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Agua", state="Jalisco", total_hectares=50.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def field(db, farm):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=15.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


# ---------------------------------------------------------------------------
# Service unit tests — pure function
# ---------------------------------------------------------------------------

def test_high_thermal_low_rain_produces_high_stress():
    """High temperature + irrigation deficit + no rain → water_stress_index near 1."""
    from cultivos.services.intelligence.water_efficiency import compute_water_efficiency

    result = compute_water_efficiency(
        hectares=10.0,
        crop_type="maiz",
        weather={"temp_c": 38.0, "humidity_pct": 20.0, "recent_rainfall_mm": 0.0},
        thermal={"stress_pct": 70.0, "irrigation_deficit": True},
    )
    assert result["water_stress_index"] >= 0.7
    assert result["liters_wasted"] >= 0
    assert result["optimal_irrigation_mm"] > 0
    assert isinstance(result["recomendacion"], str)
    assert len(result["recomendacion"]) > 10


def test_cooler_conditions_produce_lower_stress():
    """Cooler temperature + recent rain + no thermal stress → lower water_stress_index."""
    from cultivos.services.intelligence.water_efficiency import compute_water_efficiency

    result = compute_water_efficiency(
        hectares=10.0,
        crop_type="maiz",
        weather={"temp_c": 22.0, "humidity_pct": 65.0, "recent_rainfall_mm": 15.0},
        thermal={"stress_pct": 5.0, "irrigation_deficit": False},
    )
    assert result["water_stress_index"] <= 0.4
    assert isinstance(result["recomendacion"], str)


def test_stress_index_bounded_between_0_and_1():
    """water_stress_index is always in [0, 1]."""
    from cultivos.services.intelligence.water_efficiency import compute_water_efficiency

    # extreme hot
    r1 = compute_water_efficiency(
        hectares=5.0,
        crop_type="agave",
        weather={"temp_c": 45.0, "humidity_pct": 5.0, "recent_rainfall_mm": 0.0},
        thermal={"stress_pct": 100.0, "irrigation_deficit": True},
    )
    assert 0.0 <= r1["water_stress_index"] <= 1.0

    # extreme cool
    r2 = compute_water_efficiency(
        hectares=5.0,
        crop_type="agave",
        weather={"temp_c": 10.0, "humidity_pct": 90.0, "recent_rainfall_mm": 50.0},
        thermal={"stress_pct": 0.0, "irrigation_deficit": False},
    )
    assert 0.0 <= r2["water_stress_index"] <= 1.0


def test_missing_weather_degrades_gracefully():
    """Service works with no weather data — uses safe defaults."""
    from cultivos.services.intelligence.water_efficiency import compute_water_efficiency

    result = compute_water_efficiency(
        hectares=8.0,
        crop_type="frijol",
        weather=None,
        thermal=None,
    )
    assert 0.0 <= result["water_stress_index"] <= 1.0
    assert result["optimal_irrigation_mm"] > 0
    assert isinstance(result["recomendacion"], str)


def test_liters_wasted_reflects_hectares():
    """Larger field → more liters_wasted (same conditions)."""
    from cultivos.services.intelligence.water_efficiency import compute_water_efficiency

    shared = {
        "weather": {"temp_c": 35.0, "humidity_pct": 25.0, "recent_rainfall_mm": 0.0},
        "thermal": {"stress_pct": 50.0, "irrigation_deficit": True},
        "crop_type": "maiz",
    }
    r_small = compute_water_efficiency(hectares=5.0, **shared)
    r_large = compute_water_efficiency(hectares=20.0, **shared)
    assert r_large["liters_wasted"] > r_small["liters_wasted"]


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

def test_water_efficiency_no_data(client, farm, field):
    """GET returns 200 with defaults when no thermal/weather records exist."""
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/water-efficiency")
    assert resp.status_code == 200
    data = resp.json()
    assert "water_stress_index" in data
    assert "liters_wasted" in data
    assert "optimal_irrigation_mm" in data
    assert "recomendacion" in data
    assert 0.0 <= data["water_stress_index"] <= 1.0


def test_water_efficiency_with_thermal_and_weather(client, db, farm, field):
    """GET uses latest thermal + weather records to compute higher stress."""
    from datetime import datetime
    from cultivos.db.models import ThermalResult, WeatherRecord

    tr = ThermalResult(
        field_id=field.id,
        temp_mean=39.0,
        temp_std=2.0,
        temp_min=35.0,
        temp_max=43.0,
        pixels_total=10000,
        stress_pct=75.0,
        irrigation_deficit=True,
        analyzed_at=datetime(2026, 4, 10),
    )
    wr = WeatherRecord(
        farm_id=farm.id,
        temp_c=38.5,
        humidity_pct=18.0,
        wind_kmh=5.0,
        rainfall_mm=0.0,
        description="Caluroso y seco",
        recorded_at=datetime(2026, 4, 10),
    )
    db.add_all([tr, wr])
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/water-efficiency")
    assert resp.status_code == 200
    data = resp.json()
    assert data["water_stress_index"] >= 0.6


def test_water_efficiency_unknown_farm(client):
    """GET with unknown farm_id returns 404."""
    resp = client.get("/api/farms/9999/fields/1/water-efficiency")
    assert resp.status_code == 404


def test_water_efficiency_unknown_field(client, farm):
    """GET with unknown field_id returns 404."""
    resp = client.get(f"/api/farms/{farm.id}/fields/9999/water-efficiency")
    assert resp.status_code == 404
