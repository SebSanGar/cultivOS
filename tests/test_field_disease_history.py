"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/disease-history endpoint (#204).

Aggregates disease-risk triggers by month over the last N months using
WeatherRecord + NDVIResult + SoilAnalysis data. Returns monthly entries,
disease counts, recurrence flags, and months-disease-free.
"""

from datetime import datetime, timedelta

from cultivos.db.models import (
    Farm,
    Field,
    NDVIResult,
    SoilAnalysis,
    WeatherRecord,
)


def _make_farm(db, name="Rancho Historial"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Historial", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _months_ago(n_months: int) -> datetime:
    """Return a datetime mid-month, approximately N months ago."""
    return datetime.utcnow() - timedelta(days=30 * n_months + 5)


def _add_weather(db, farm_id, humidity=50.0, temp=25.0, months_ago=1):
    w = WeatherRecord(
        farm_id=farm_id,
        temp_c=temp,
        humidity_pct=humidity,
        wind_kmh=5.0,
        rainfall_mm=0.0,
        description="test",
        forecast_3day=[],
        recorded_at=_months_ago(months_ago),
    )
    db.add(w)
    db.commit()
    return w


def _add_soil(db, field_id, ph=6.5, months_ago=1):
    s = SoilAnalysis(
        field_id=field_id,
        ph=ph,
        organic_matter_pct=3.0,
        nitrogen_ppm=10.0,
        phosphorus_ppm=10.0,
        potassium_ppm=10.0,
        sampled_at=_months_ago(months_ago),
        created_at=_months_ago(months_ago),
    )
    db.add(s)
    db.commit()
    return s


def test_disease_history_404(client, db):
    # Unknown farm
    r = client.get("/api/farms/9999/fields/1/disease-history")
    assert r.status_code == 404

    # Unknown field under existing farm
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/9999/disease-history")
    assert r.status_code == 404


def test_disease_history_clean_field(client, db):
    """No weather/NDVI/soil → every month is disease-free."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/disease-history?months=6"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["farm_id"] == farm.id
    assert data["field_id"] == field.id
    assert data["total_months_analyzed"] == 6
    assert data["months_disease_free"] == 6
    assert data["most_common_disease"] is None
    assert data["recurrence_detected"] is False
    assert data["recurring_diseases"] == []
    assert data["disease_counts"] == {}
    assert len(data["monthly"]) == 6
    for entry in data["monthly"]:
        assert entry["diseases"] == []
        assert entry["triggers"] == []
        assert entry["disease_count"] == 0


def test_disease_history_basic(client, db):
    """One month with high humidity → one disease, no recurrence."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    _add_weather(db, farm.id, humidity=85.0, temp=25.0, months_ago=2)

    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/disease-history?months=12"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total_months_analyzed"] == 12
    assert data["months_disease_free"] == 11
    assert data["most_common_disease"] == "Tizón tardío"
    assert data["disease_counts"] == {"Tizón tardío": 1}
    assert data["recurrence_detected"] is False
    assert data["recurring_diseases"] == []

    triggered_months = [m for m in data["monthly"] if m["disease_count"] > 0]
    assert len(triggered_months) == 1
    assert "humidity" in triggered_months[0]["triggers"]
    assert "Tizón tardío" in triggered_months[0]["diseases"]


def test_disease_history_recurrence(client, db):
    """Same disease in 3 different months → recurrence detected."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    for m in (1, 3, 5):
        _add_weather(db, farm.id, humidity=85.0, temp=25.0, months_ago=m)

    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/disease-history?months=12"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["disease_counts"]["Tizón tardío"] == 3
    assert data["recurrence_detected"] is True
    assert "Tizón tardío" in data["recurring_diseases"]
    assert data["most_common_disease"] == "Tizón tardío"
    assert data["months_disease_free"] == 12 - 3


def test_disease_history_months_param(client, db):
    """months=3 → only 3 months analyzed; triggers outside window ignored."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    # Trigger inside 3-month window
    _add_weather(db, farm.id, humidity=85.0, months_ago=1)
    # Trigger outside 3-month window (should be ignored)
    _add_weather(db, farm.id, humidity=85.0, months_ago=8)

    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/disease-history?months=3"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total_months_analyzed"] == 3
    assert len(data["monthly"]) == 3
    assert data["disease_counts"].get("Tizón tardío") == 1


def test_disease_history_multi_trigger(client, db):
    """Acid soil + hot weather in same month → both diseases counted."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)

    _add_weather(db, farm.id, humidity=50.0, temp=38.0, months_ago=2)
    _add_soil(db, field.id, ph=5.0, months_ago=2)

    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/disease-history?months=6"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["disease_counts"].get("Estrés por calor") == 1
    assert data["disease_counts"].get("Marchitez por Fusarium") == 1
    triggered = [m for m in data["monthly"] if m["disease_count"] > 0]
    assert len(triggered) == 1
    assert set(triggered[0]["triggers"]) == {"temp", "ph"}
    assert triggered[0]["disease_count"] == 2
