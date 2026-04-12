"""Tests for GET /api/cooperatives/{coop_id}/sensor-freshness

Task #196: Cooperative sensor freshness rollup.
Composes compute_sensor_freshness per member farm and aggregates.
"""

from datetime import datetime, timedelta

from cultivos.db.models import (
    Cooperative,
    Farm,
    Field,
    HealthScore,
    NDVIResult,
    SoilAnalysis,
    WeatherRecord,
)


def _coop(db, name="Coop Freshness"):
    c = Cooperative(name=name, state="Jalisco")
    db.add(c)
    db.flush()
    return c


def _farm(db, coop_id=None, name="Finca"):
    f = Farm(name=name, state="Jalisco", total_hectares=10.0, cooperative_id=coop_id)
    db.add(f)
    db.flush()
    return f


def _field(db, farm_id, name="Lote"):
    fld = Field(farm_id=farm_id, name=name, hectares=5.0, crop_type="maiz")
    db.add(fld)
    db.flush()
    return fld


def _ndvi(db, field_id, days_ago):
    db.add(NDVIResult(
        field_id=field_id,
        ndvi_mean=0.6, ndvi_std=0.05, ndvi_min=0.4, ndvi_max=0.8,
        pixels_total=1000, stress_pct=5.0, zones=[],
        analyzed_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.flush()


def _soil(db, field_id, days_ago):
    db.add(SoilAnalysis(
        field_id=field_id,
        ph=6.5, organic_matter_pct=2.0,
        nitrogen_ppm=20, phosphorus_ppm=15, potassium_ppm=180,
        sampled_at=datetime.utcnow() - timedelta(days=days_ago),
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.flush()


def _health(db, field_id, days_ago):
    db.add(HealthScore(
        field_id=field_id,
        score=78.0,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.flush()


def _weather(db, farm_id, days_ago):
    db.add(WeatherRecord(
        farm_id=farm_id,
        temp_c=24.0, humidity_pct=55.0, wind_kmh=8.0,
        rainfall_mm=0.0, description="soleado",
        recorded_at=datetime.utcnow() - timedelta(days=days_ago),
    ))
    db.flush()


def _seed_fresh_field(db, farm_id, field_name="Lote"):
    fld = _field(db, farm_id, name=field_name)
    _ndvi(db, fld.id, 2)
    _soil(db, fld.id, 3)
    _health(db, fld.id, 1)
    return fld


def test_404_unknown_cooperative(client, db):
    r = client.get("/api/cooperatives/9999/sensor-freshness")
    assert r.status_code == 404


def test_empty_cooperative(client, db):
    c = _coop(db)
    db.commit()
    r = client.get(f"/api/cooperatives/{c.id}/sensor-freshness")
    assert r.status_code == 200
    body = r.json()
    assert body["cooperative_id"] == c.id
    assert body["farms_count"] == 0
    assert body["total_fields"] == 0
    assert body["fields_with_stale_sensors"] == 0
    assert body["avg_days_since_last_signal"] == {
        "ndvi": None, "soil": None, "health": None, "weather": None,
    }
    assert body["worst_farm"] is None
    assert body["farms"] == []


def test_single_farm_all_fresh(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id, name="Finca Fresca")
    _seed_fresh_field(db, f.id)
    _weather(db, f.id, 1)
    db.commit()

    r = client.get(f"/api/cooperatives/{c.id}/sensor-freshness")
    body = r.json()
    assert body["farms_count"] == 1
    assert body["total_fields"] == 1
    assert body["fields_with_stale_sensors"] == 0
    avg = body["avg_days_since_last_signal"]
    assert avg["ndvi"] == 2.0
    assert avg["soil"] == 3.0
    assert avg["health"] == 1.0
    assert avg["weather"] == 1.0
    # worst_farm is still populated (the only farm) but stale_fields=0
    assert body["worst_farm"] is not None
    assert body["worst_farm"]["stale_fields"] == 0
    assert len(body["farms"]) == 1
    assert body["farms"][0]["farm_id"] == f.id
    assert body["farms"][0]["total_fields"] == 1
    assert body["farms"][0]["stale_fields"] == 0


def test_single_farm_all_stale(client, db):
    c = _coop(db)
    f = _farm(db, coop_id=c.id, name="Finca Rancia")
    _field(db, f.id)  # field with NO sensor data → all stale
    db.commit()

    r = client.get(f"/api/cooperatives/{c.id}/sensor-freshness")
    body = r.json()
    assert body["total_fields"] == 1
    assert body["fields_with_stale_sensors"] == 1
    avg = body["avg_days_since_last_signal"]
    # All None since no data — no samples to average
    assert avg["ndvi"] is None
    assert avg["soil"] is None
    assert avg["health"] is None
    assert avg["weather"] is None
    assert body["farms"][0]["stale_fields"] == 1
    assert body["farms"][0]["stale_fields_pct"] == 100.0


def test_multi_farm_aggregation_and_worst_farm(client, db):
    c = _coop(db)
    f1 = _farm(db, coop_id=c.id, name="Finca A")
    f2 = _farm(db, coop_id=c.id, name="Finca B")
    # Farm A: 2 fields, both fresh
    _seed_fresh_field(db, f1.id, "A1")
    _seed_fresh_field(db, f1.id, "A2")
    _weather(db, f1.id, 2)
    # Farm B: 2 fields, both have NO sensor data → fully stale
    _field(db, f2.id, name="B1")
    _field(db, f2.id, name="B2")
    db.commit()

    r = client.get(f"/api/cooperatives/{c.id}/sensor-freshness")
    body = r.json()
    assert body["farms_count"] == 2
    assert body["total_fields"] == 4
    assert body["fields_with_stale_sensors"] == 2
    # worst_farm is B (100% stale)
    assert body["worst_farm"]["farm_id"] == f2.id
    assert body["worst_farm"]["stale_fields"] == 2
    assert body["worst_farm"]["stale_fields_pct"] == 100.0
    farms_by_id = {fm["farm_id"]: fm for fm in body["farms"]}
    assert farms_by_id[f1.id]["stale_fields"] == 0
    assert farms_by_id[f2.id]["stale_fields"] == 2


def test_avg_excludes_none_values(client, db):
    """avg_days_since_last_signal is computed only from fields with data."""
    c = _coop(db)
    f = _farm(db, coop_id=c.id)
    # One field with NDVI day=4, other with NDVI day=10
    fld1 = _field(db, f.id, name="F1")
    fld2 = _field(db, f.id, name="F2")
    _ndvi(db, fld1.id, 4)
    _ndvi(db, fld2.id, 10)
    db.commit()

    r = client.get(f"/api/cooperatives/{c.id}/sensor-freshness")
    body = r.json()
    assert body["avg_days_since_last_signal"]["ndvi"] == 7.0
    # Other sensors never seeded → None
    assert body["avg_days_since_last_signal"]["soil"] is None


def test_unaffiliated_farm_excluded(client, db):
    c = _coop(db)
    _farm(db, coop_id=c.id, name="In")
    # Orphan farm — not in coop
    other = _farm(db, coop_id=None, name="Out")
    _seed_fresh_field(db, other.id)
    db.commit()

    r = client.get(f"/api/cooperatives/{c.id}/sensor-freshness")
    body = r.json()
    assert body["farms_count"] == 1
    assert all(fm["farm_id"] != other.id for fm in body["farms"])


def test_other_cooperative_excluded(client, db):
    c1 = _coop(db, name="Own")
    c2 = _coop(db, name="Other")
    f2 = _farm(db, coop_id=c2.id, name="Otra")
    _seed_fresh_field(db, f2.id)
    db.commit()

    r = client.get(f"/api/cooperatives/{c1.id}/sensor-freshness")
    body = r.json()
    assert body["farms_count"] == 0
    assert body["total_fields"] == 0
