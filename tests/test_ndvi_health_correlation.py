"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/ndvi-health-correlation (#212).

Pearson correlation between HealthScore.ndvi_mean and HealthScore.score over a
rolling window. Strength tiers: |r|>=0.7 strong, 0.4-0.7 moderate, 0.15-0.4 weak,
<0.15 none. Fewer than 5 valid samples → insufficient_data.
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore


def _make_farm(db, name="Rancho Correlacion"):
    farm = Farm(name=name, state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Parcela Corr", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
    db.add(field)
    db.commit()
    return field


def _add_health(db, field_id, *, days_ago: int, score: float, ndvi_mean: float | None):
    hs = HealthScore(
        field_id=field_id,
        score=score,
        ndvi_mean=ndvi_mean,
        scored_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(hs)
    db.commit()
    return hs


def test_correlation_404_farm(client):
    r = client.get("/api/farms/9999/fields/1/ndvi-health-correlation")
    assert r.status_code == 404


def test_correlation_404_field(client, db):
    farm = _make_farm(db)
    r = client.get(f"/api/farms/{farm.id}/fields/9999/ndvi-health-correlation")
    assert r.status_code == 404


def test_correlation_no_samples(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/ndvi-health-correlation"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["field_id"] == field.id
    assert body["sample_size"] == 0
    assert body["correlation"] is None
    assert body["strength"] == "insufficient_data"
    assert "insuficiente" in body["interpretation_es"].lower()


def test_correlation_insufficient_data(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Only 4 valid samples → below 5 minimum
    for i, (s, n) in enumerate([(70, 0.6), (72, 0.62), (74, 0.64), (76, 0.66)]):
        _add_health(db, field.id, days_ago=i + 1, score=s, ndvi_mean=n)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/ndvi-health-correlation"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sample_size"] == 4
    assert body["strength"] == "insufficient_data"
    assert body["correlation"] is None


def test_correlation_strong_positive(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Perfectly monotone increasing pair → r == 1
    pairs = [(50, 0.40), (55, 0.45), (60, 0.50), (65, 0.55), (70, 0.60), (75, 0.65)]
    for i, (s, n) in enumerate(pairs):
        _add_health(db, field.id, days_ago=i + 1, score=s, ndvi_mean=n)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/ndvi-health-correlation"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sample_size"] == 6
    assert body["correlation"] is not None
    assert body["correlation"] >= 0.95
    assert body["strength"] == "strong"
    assert body["mean_health"] == 62.5
    assert round(body["mean_ndvi"], 4) == 0.525


def test_correlation_strong_negative(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    pairs = [(80, 0.30), (75, 0.40), (70, 0.50), (65, 0.60), (60, 0.70), (55, 0.80)]
    for i, (s, n) in enumerate(pairs):
        _add_health(db, field.id, days_ago=i + 1, score=s, ndvi_mean=n)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/ndvi-health-correlation"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["correlation"] is not None
    assert body["correlation"] <= -0.95
    assert body["strength"] == "strong"
    assert "inversa" in body["interpretation_es"].lower()


def test_correlation_weak(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Noisy pairs designed for weak correlation (|r| roughly 0.15-0.4)
    pairs = [(60, 0.5), (70, 0.48), (65, 0.55), (72, 0.52), (68, 0.50), (74, 0.53)]
    for i, (s, n) in enumerate(pairs):
        _add_health(db, field.id, days_ago=i + 1, score=s, ndvi_mean=n)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/ndvi-health-correlation"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sample_size"] == 6
    assert body["strength"] in ("weak", "moderate", "none")


def test_correlation_filters_out_of_window(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # 6 in-window samples
    for i, (s, n) in enumerate([(50, 0.40), (55, 0.45), (60, 0.50), (65, 0.55), (70, 0.60), (75, 0.65)]):
        _add_health(db, field.id, days_ago=i + 1, score=s, ndvi_mean=n)
    # Old samples outside 30-day window should be excluded
    _add_health(db, field.id, days_ago=200, score=10, ndvi_mean=0.9)
    _add_health(db, field.id, days_ago=250, score=95, ndvi_mean=0.1)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/ndvi-health-correlation?days=30"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["period_days"] == 30
    assert body["sample_size"] == 6
    assert body["correlation"] >= 0.95


def test_correlation_skips_null_ndvi(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    # Mix: 5 valid + 2 with null ndvi_mean (should be skipped)
    for i, (s, n) in enumerate([(50, 0.40), (55, 0.45), (60, 0.50), (65, 0.55), (70, 0.60)]):
        _add_health(db, field.id, days_ago=i + 1, score=s, ndvi_mean=n)
    _add_health(db, field.id, days_ago=6, score=80, ndvi_mean=None)
    _add_health(db, field.id, days_ago=7, score=40, ndvi_mean=None)
    r = client.get(
        f"/api/farms/{farm.id}/fields/{field.id}/ndvi-health-correlation"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sample_size"] == 5
    assert body["correlation"] >= 0.95
