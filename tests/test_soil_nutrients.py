"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/soil-nutrients endpoint (#220)."""

import pytest
from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, SoilAnalysis


def _make_farm(db):
    farm = Farm(name="Test Farm", municipality="Guadalajara", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id):
    field = Field(farm_id=farm_id, name="Lote A", crop_type="maiz", hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_soil(db, field_id, n=None, p=None, k=None, om=None, months_ago=0):
    sampled_at = datetime.utcnow() - timedelta(days=months_ago * 30)
    sa = SoilAnalysis(
        field_id=field_id,
        nitrogen_ppm=n,
        phosphorus_ppm=p,
        potassium_ppm=k,
        organic_matter_pct=om,
        sampled_at=sampled_at,
    )
    db.add(sa)
    db.commit()
    return sa


def test_404_unknown_farm(client, db):
    r = client.get("/api/farms/99999/fields/99999/soil-nutrients")
    assert r.status_code == 404


def test_404_unknown_field(client, db):
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/99999/soil-nutrients")
    assert r.status_code == 404


def test_no_soil_data_returns_empty_stable(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-nutrients")
    assert r.status_code == 200
    data = r.json()
    assert data["field_id"] == field.id
    assert data["window_months"] == 12
    assert data["months"] == []
    assert data["nitrogen_trend"] == "stable"
    assert data["phosphorus_trend"] == "stable"
    assert data["potassium_trend"] == "stable"
    assert data["organic_matter_trend"] == "stable"


def test_response_schema_keys(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, n=20.0, p=15.0, k=100.0, om=3.0, months_ago=1)
    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-nutrients")
    assert r.status_code == 200
    data = r.json()
    for key in ("field_id", "window_months", "months",
                "nitrogen_trend", "phosphorus_trend",
                "potassium_trend", "organic_matter_trend"):
        assert key in data
    month = data["months"][0]
    for key in ("month_label", "avg_nitrogen_ppm", "avg_phosphorus_ppm",
                "avg_potassium_ppm", "avg_organic_matter_pct"):
        assert key in month


def test_three_months_averaged_values(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Two samples in the same month should be averaged
    _add_soil(db, field.id, n=20.0, p=10.0, k=80.0, om=2.0, months_ago=2)
    _add_soil(db, field.id, n=30.0, p=20.0, k=120.0, om=3.0, months_ago=1)
    _add_soil(db, field.id, n=32.0, p=22.0, k=128.0, om=3.2, months_ago=1)
    _add_soil(db, field.id, n=40.0, p=30.0, k=160.0, om=4.0, months_ago=0)

    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-nutrients")
    assert r.status_code == 200
    months = r.json()["months"]
    assert len(months) == 3
    # middle month is average of 30 and 32 for N
    middle = months[1]
    assert middle["avg_nitrogen_ppm"] == pytest.approx(31.0, abs=0.01)
    assert middle["avg_phosphorus_ppm"] == pytest.approx(21.0, abs=0.01)


def test_nitrogen_trend_improving(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, n=10.0, months_ago=4)
    _add_soil(db, field.id, n=12.0, months_ago=3)
    _add_soil(db, field.id, n=25.0, months_ago=1)
    _add_soil(db, field.id, n=28.0, months_ago=0)
    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-nutrients")
    assert r.json()["nitrogen_trend"] == "improving"


def test_potassium_trend_declining(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, k=150.0, months_ago=4)
    _add_soil(db, field.id, k=145.0, months_ago=3)
    _add_soil(db, field.id, k=90.0, months_ago=1)
    _add_soil(db, field.id, k=85.0, months_ago=0)
    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-nutrients")
    assert r.json()["potassium_trend"] == "declining"


def test_records_outside_window_excluded(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # 14 months ago — outside default 12-month window
    _add_soil(db, field.id, n=5.0, p=5.0, k=5.0, om=1.0, months_ago=14)
    _add_soil(db, field.id, n=25.0, p=15.0, k=110.0, om=3.0, months_ago=1)
    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-nutrients")
    data = r.json()
    assert len(data["months"]) == 1
    assert data["months"][0]["avg_nitrogen_ppm"] == pytest.approx(25.0, abs=0.01)


def test_default_window_is_12_months(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-nutrients")
    assert r.json()["window_months"] == 12


def test_months_param_narrows_window(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _add_soil(db, field.id, n=20.0, months_ago=5)  # outside 3-month window
    _add_soil(db, field.id, n=30.0, months_ago=1)  # inside
    r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/soil-nutrients?months=3")
    data = r.json()
    assert data["window_months"] == 3
    assert len(data["months"]) == 1
    assert data["months"][0]["avg_nitrogen_ppm"] == pytest.approx(30.0, abs=0.01)
