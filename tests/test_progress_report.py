"""Tests for GET /api/farms/{farm_id}/progress-report."""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Progreso"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Uno", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type)
    db.add(field)
    db.commit()
    return field


def _make_health(db, field_id, score, at):
    h = HealthScore(
        field_id=field_id,
        score=score,
        sources=["ndvi"],
        breakdown={},
        scored_at=at,
    )
    db.add(h)
    db.commit()
    return h


def _make_ndvi(db, field_id, mean, at):
    n = NDVIResult(
        field_id=field_id,
        ndvi_mean=mean,
        ndvi_std=0.05,
        ndvi_min=0.3,
        ndvi_max=0.9,
        pixels_total=1000,
        stress_pct=5.0,
        zones=[{"zone": "A", "mean": mean}],
        analyzed_at=at,
    )
    db.add(n)
    db.commit()
    return n


def _make_soil(db, field_id, ph, at):
    s = SoilAnalysis(
        field_id=field_id,
        ph=ph,
        sampled_at=at,
    )
    db.add(s)
    db.commit()
    return s


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 404


def test_response_top_level_keys(client, db):
    """Response contains required top-level keys."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "period_start" in data
    assert "period_end" in data
    assert "fields" in data
    assert "farms_improved_pct" in data


def test_no_data_in_period_returns_empty_fields(client, db):
    """Farm exists but has no data in date range → fields = [], farms_improved_pct = 0."""
    farm = _make_farm(db)
    _make_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    data = resp.json()
    assert data["fields"] == []
    assert data["farms_improved_pct"] == 0.0


def test_field_entry_keys_present(client, db):
    """Each field entry has required keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    mid = datetime(2026, 2, 14)
    _make_health(db, field.id, score=50.0, at=datetime(2026, 1, 10))
    _make_health(db, field.id, score=70.0, at=datetime(2026, 3, 20))

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    entry = resp.json()["fields"][0]
    assert "field_id" in entry
    assert "field_name" in entry
    assert "health_delta" in entry
    assert "ndvi_delta" in entry
    assert "soil_ph_delta" in entry
    assert "improved" in entry


def test_rising_health_gives_positive_delta(client, db):
    """Health improves from first half to second half → health_delta > 0, improved = True."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # period: 2026-01-01 → 2026-03-31 (midpoint ~2026-02-14)
    _make_health(db, field.id, score=40.0, at=datetime(2026, 1, 15))  # first half
    _make_health(db, field.id, score=80.0, at=datetime(2026, 3, 15))  # second half

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    entry = resp.json()["fields"][0]
    assert entry["health_delta"] > 0
    assert entry["improved"] is True


def test_declining_health_gives_negative_delta(client, db):
    """Health declines from first half to second half → health_delta < 0, improved = False."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, score=80.0, at=datetime(2026, 1, 15))  # first half
    _make_health(db, field.id, score=40.0, at=datetime(2026, 3, 15))  # second half

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    entry = resp.json()["fields"][0]
    assert entry["health_delta"] < 0
    assert entry["improved"] is False


def test_health_delta_math(client, db):
    """health_delta = avg(second_half) - avg(first_half)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # period: 2026-01-01 → 2026-02-28 (midpoint ~2026-01-30)
    _make_health(db, field.id, score=60.0, at=datetime(2026, 1, 10))  # first half
    _make_health(db, field.id, score=80.0, at=datetime(2026, 1, 20))  # first half avg=70
    _make_health(db, field.id, score=90.0, at=datetime(2026, 2, 15))  # second half avg=90

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-02-28")
    assert resp.status_code == 200
    entry = resp.json()["fields"][0]
    # delta = 90 - 70 = 20
    assert abs(entry["health_delta"] - 20.0) < 1.0


def test_ndvi_delta_computed(client, db):
    """ndvi_delta = avg(second_half ndvi_mean) - avg(first_half ndvi_mean)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_ndvi(db, field.id, mean=0.4, at=datetime(2026, 1, 15))   # first half
    _make_ndvi(db, field.id, mean=0.7, at=datetime(2026, 3, 15))   # second half

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    entry = resp.json()["fields"][0]
    assert entry["ndvi_delta"] is not None
    assert abs(entry["ndvi_delta"] - 0.3) < 0.01


def test_soil_ph_delta_computed(client, db):
    """soil_ph_delta = avg(second_half ph) - avg(first_half ph)."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_soil(db, field.id, ph=5.5, at=datetime(2026, 1, 15))
    _make_soil(db, field.id, ph=6.5, at=datetime(2026, 3, 15))

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    entry = resp.json()["fields"][0]
    assert entry["soil_ph_delta"] is not None
    assert abs(entry["soil_ph_delta"] - 1.0) < 0.01


def test_missing_ndvi_returns_none_delta(client, db):
    """Field with no NDVI data → ndvi_delta = None."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, score=60.0, at=datetime(2026, 1, 15))
    _make_health(db, field.id, score=80.0, at=datetime(2026, 3, 15))

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    entry = resp.json()["fields"][0]
    assert entry["ndvi_delta"] is None


def test_farms_improved_pct_correct(client, db):
    """2 fields: one improved, one declined → farms_improved_pct = 50.0."""
    farm = _make_farm(db)
    field1 = _make_field(db, farm.id, name="Campo Uno")
    field2 = _make_field(db, farm.id, name="Campo Dos")

    # field1: improving
    _make_health(db, field1.id, score=40.0, at=datetime(2026, 1, 15))
    _make_health(db, field1.id, score=80.0, at=datetime(2026, 3, 15))
    # field2: declining
    _make_health(db, field2.id, score=80.0, at=datetime(2026, 1, 15))
    _make_health(db, field2.id, score=40.0, at=datetime(2026, 3, 15))

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    data = resp.json()
    assert abs(data["farms_improved_pct"] - 50.0) < 1.0


def test_data_only_in_one_half_gives_none_delta(client, db):
    """Health data only in first half, none in second half → health_delta = None, improved = None."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Only first-half data
    _make_health(db, field.id, score=60.0, at=datetime(2026, 1, 10))

    resp = client.get(f"/api/farms/{farm.id}/progress-report?start_date=2026-01-01&end_date=2026-03-31")
    assert resp.status_code == 200
    data = resp.json()
    # field appears but deltas are None since one half is empty
    if data["fields"]:
        entry = data["fields"][0]
        assert entry["health_delta"] is None
        assert entry["improved"] is None
