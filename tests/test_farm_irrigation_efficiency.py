"""Tests for farm irrigation efficiency aggregate.

GET /api/farms/{farm_id}/irrigation-efficiency — composes water_efficiency
across all fields of the farm.
"""

from datetime import datetime

import pytest


@pytest.fixture
def farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Riego", state="Jalisco", total_hectares=80.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@pytest.fixture
def other_farm(db):
    from cultivos.db.models import Farm
    f = Farm(name="Rancho Vecino", state="Jalisco", total_hectares=30.0)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _make_field(db, farm, name, crop="maiz", ha=10.0):
    from cultivos.db.models import Field
    f = Field(farm_id=farm.id, name=name, crop_type=crop, hectares=ha)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _add_hot_dry(db, farm, field):
    from cultivos.db.models import ThermalResult, WeatherRecord
    db.add_all([
        ThermalResult(
            field_id=field.id,
            temp_mean=39.0,
            temp_std=2.0,
            temp_min=35.0,
            temp_max=43.0,
            pixels_total=10000,
            stress_pct=75.0,
            irrigation_deficit=True,
            analyzed_at=datetime(2026, 4, 10),
        ),
        WeatherRecord(
            farm_id=farm.id,
            temp_c=38.5,
            humidity_pct=18.0,
            wind_kmh=5.0,
            rainfall_mm=0.0,
            description="Caluroso y seco",
            recorded_at=datetime(2026, 4, 10),
        ),
    ])
    db.commit()


def test_irrigation_efficiency_unknown_farm(client):
    resp = client.get("/api/farms/9999/irrigation-efficiency")
    assert resp.status_code == 404


def test_irrigation_efficiency_empty_farm(client, farm):
    resp = client.get(f"/api/farms/{farm.id}/irrigation-efficiency")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["total_fields"] == 0
    assert data["avg_water_efficiency_pct"] is None
    assert data["fields_below_70pct"] == 0
    assert data["worst_field"] is None
    assert data["fields"] == []


def test_irrigation_efficiency_single_stressed_field(client, db, farm):
    field = _make_field(db, farm, "Parcela Seca", crop="maiz", ha=12.0)
    _add_hot_dry(db, farm, field)

    resp = client.get(f"/api/farms/{farm.id}/irrigation-efficiency")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_fields"] == 1
    assert len(data["fields"]) == 1
    item = data["fields"][0]
    assert item["field_id"] == field.id
    assert item["field_name"] == "Parcela Seca"
    assert item["crop_type"] == "maiz"
    # Hot/dry/deficit → high stress → low efficiency
    assert item["efficiency_pct"] <= 30.0
    assert item["water_stress_index"] >= 0.7
    assert item["optimal_irrigation_mm"] > 0

    assert data["avg_water_efficiency_pct"] == item["efficiency_pct"]
    assert data["fields_below_70pct"] == 1
    assert data["worst_field"] is not None
    assert data["worst_field"]["field_id"] == field.id
    assert data["worst_field"]["efficiency_pct"] == item["efficiency_pct"]


def test_irrigation_efficiency_graceful_no_data(client, db, farm):
    """Field with no thermal/weather rows still computes via service defaults."""
    field = _make_field(db, farm, "Parcela Neutra", crop="frijol", ha=8.0)
    resp = client.get(f"/api/farms/{farm.id}/irrigation-efficiency")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_fields"] == 1
    item = data["fields"][0]
    assert 0.0 <= item["water_stress_index"] <= 1.0
    assert 0.0 <= item["efficiency_pct"] <= 100.0
    assert data["avg_water_efficiency_pct"] is not None


def test_irrigation_efficiency_multi_field_aggregate(client, db, farm):
    stressed = _make_field(db, farm, "Parcela Seca", crop="maiz", ha=10.0)
    _add_hot_dry(db, farm, stressed)
    _make_field(db, farm, "Parcela Tranquila", crop="frijol", ha=6.0)
    _make_field(db, farm, "Parcela Intermedia", crop="agave", ha=4.0)

    resp = client.get(f"/api/farms/{farm.id}/irrigation-efficiency")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_fields"] == 3
    assert len(data["fields"]) == 3

    effs = [f["efficiency_pct"] for f in data["fields"]]
    expected_avg = round(sum(effs) / 3, 1)
    assert data["avg_water_efficiency_pct"] == expected_avg

    # At least the hot/dry field is below 70%
    assert data["fields_below_70pct"] >= 1
    assert data["worst_field"] is not None
    assert data["worst_field"]["field_id"] == stressed.id
    # worst_field efficiency should be the minimum across items
    assert data["worst_field"]["efficiency_pct"] == min(effs)


def test_irrigation_efficiency_excludes_other_farm(client, db, farm, other_farm):
    own = _make_field(db, farm, "Propia", crop="maiz", ha=5.0)
    _add_hot_dry(db, farm, own)
    foreign = _make_field(db, other_farm, "Ajena", crop="maiz", ha=5.0)
    _add_hot_dry(db, other_farm, foreign)

    resp = client.get(f"/api/farms/{farm.id}/irrigation-efficiency")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_fields"] == 1
    assert data["fields"][0]["field_id"] == own.id
