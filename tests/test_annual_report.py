"""Tests for GET /api/farms/{farm_id}/annual-report."""

from datetime import datetime

from cultivos.db.models import (
    CarbonBaseline,
    Farm,
    Field,
    HealthScore,
    NDVIResult,
    SoilAnalysis,
    TreatmentRecord,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Anual"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo A", crop_type="maiz"):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=5.0)
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
    s = SoilAnalysis(field_id=field_id, ph=ph, sampled_at=at)
    db.add(s)
    db.commit()
    return s


def _make_treatment(db, field_id, organic=True, at=None):
    t = TreatmentRecord(
        field_id=field_id,
        health_score_used=60.0,
        problema="plaga",
        causa_probable="humedad",
        tratamiento="neem",
        costo_estimado_mxn=100,
        urgencia="media",
        prevencion="rotacion",
        organic=organic,
        applied_at=at or datetime(2025, 6, 1),
    )
    db.add(t)
    db.commit()
    return t


def _make_carbon_baseline(db, field_id, soc_percent=2.5, date_str="2025-06-01"):
    cb = CarbonBaseline(
        field_id=field_id,
        soc_percent=soc_percent,
        measurement_date=date_str,
        lab_method="dry_combustion",
    )
    db.add(cb)
    db.commit()
    return cb


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/annual-report?year=2025")
    assert resp.status_code == 404


def test_response_top_level_keys(client, db):
    """Response contains required top-level keys."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "farm_id" in data
    assert "year" in data
    assert "fields" in data
    assert "best_field" in data
    assert "most_improved_field" in data
    assert "total_co2e_sequestered_t" in data
    assert "treatments_applied_total" in data


def test_year_defaults_to_current(client, db):
    """Omitting year parameter uses current year."""
    farm = _make_farm(db)
    resp = client.get(f"/api/farms/{farm.id}/annual-report")
    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == datetime.utcnow().year


def test_empty_year_returns_graceful_empty(client, db):
    """Farm with no data in requested year → empty fields, nulls for aggregates."""
    farm = _make_farm(db)
    _make_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert data["fields"] == []
    assert data["best_field"] is None
    assert data["most_improved_field"] is None
    assert data["total_co2e_sequestered_t"] == 0.0
    assert data["treatments_applied_total"] == 0


def test_field_entry_keys_present(client, db):
    """Each field entry has all required keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, 70.0, datetime(2025, 3, 1))

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    entry = resp.json()["fields"][0]
    assert "field_id" in entry
    assert "field_name" in entry
    assert "avg_health" in entry
    assert "min_health" in entry
    assert "max_health" in entry
    assert "ndvi_trend" in entry
    assert "soil_ph_delta" in entry
    assert "treatments_applied" in entry
    assert "regen_score" in entry


def test_health_avg_min_max_computed(client, db):
    """avg/min/max health computed correctly for the year."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, 40.0, datetime(2025, 2, 1))
    _make_health(db, field.id, 60.0, datetime(2025, 6, 1))
    _make_health(db, field.id, 80.0, datetime(2025, 10, 1))

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    entry = resp.json()["fields"][0]
    assert abs(entry["avg_health"] - 60.0) < 0.01
    assert entry["min_health"] == 40.0
    assert entry["max_health"] == 80.0


def test_year_filter_excludes_other_years(client, db):
    """Health scores outside year are excluded."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_health(db, field.id, 50.0, datetime(2024, 6, 1))  # excluded
    _make_health(db, field.id, 80.0, datetime(2025, 6, 1))  # included
    _make_health(db, field.id, 30.0, datetime(2026, 6, 1))  # excluded

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    entry = resp.json()["fields"][0]
    assert entry["avg_health"] == 80.0
    assert entry["min_health"] == 80.0
    assert entry["max_health"] == 80.0


def test_ndvi_trend_first_vs_last(client, db):
    """ndvi_trend = last ndvi_mean - first ndvi_mean within year."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_ndvi(db, field.id, mean=0.4, at=datetime(2025, 1, 10))
    _make_ndvi(db, field.id, mean=0.8, at=datetime(2025, 11, 10))

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    entry = resp.json()["fields"][0]
    assert entry["ndvi_trend"] is not None
    assert abs(entry["ndvi_trend"] - 0.4) < 0.01


def test_soil_ph_delta_first_vs_last(client, db):
    """soil_ph_delta = last ph - first ph within year."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_soil(db, field.id, ph=5.5, at=datetime(2025, 2, 1))
    _make_soil(db, field.id, ph=6.8, at=datetime(2025, 10, 1))

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    entry = resp.json()["fields"][0]
    assert entry["soil_ph_delta"] is not None
    assert abs(entry["soil_ph_delta"] - 1.3) < 0.01


def test_treatments_applied_count(client, db):
    """treatments_applied = count of treatments applied in year."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_treatment(db, field.id, organic=True, at=datetime(2025, 3, 1))
    _make_treatment(db, field.id, organic=True, at=datetime(2025, 6, 1))
    _make_treatment(db, field.id, organic=False, at=datetime(2025, 9, 1))
    _make_treatment(db, field.id, organic=True, at=datetime(2024, 3, 1))  # excluded

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    entry = resp.json()["fields"][0]
    assert entry["treatments_applied"] == 3


def test_regen_score_percent_organic(client, db):
    """regen_score = % of treatments that are organic."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _make_treatment(db, field.id, organic=True, at=datetime(2025, 3, 1))
    _make_treatment(db, field.id, organic=True, at=datetime(2025, 4, 1))
    _make_treatment(db, field.id, organic=True, at=datetime(2025, 5, 1))
    _make_treatment(db, field.id, organic=False, at=datetime(2025, 6, 1))

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    entry = resp.json()["fields"][0]
    assert abs(entry["regen_score"] - 75.0) < 0.01


def test_best_field_highest_avg_health(client, db):
    """best_field is the field with highest avg_health."""
    farm = _make_farm(db)
    f1 = _make_field(db, farm.id, name="Campo Bajo")
    f2 = _make_field(db, farm.id, name="Campo Alto")
    _make_health(db, f1.id, 40.0, datetime(2025, 6, 1))
    _make_health(db, f2.id, 90.0, datetime(2025, 6, 1))

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    data = resp.json()
    assert data["best_field"] == "Campo Alto"


def test_most_improved_field(client, db):
    """most_improved_field has the biggest positive delta (last - first health) in year."""
    farm = _make_farm(db)
    f1 = _make_field(db, farm.id, name="Campo Flat")
    f2 = _make_field(db, farm.id, name="Campo Rising")
    # f1: flat
    _make_health(db, f1.id, 70.0, datetime(2025, 1, 1))
    _make_health(db, f1.id, 72.0, datetime(2025, 12, 1))
    # f2: rising big
    _make_health(db, f2.id, 40.0, datetime(2025, 1, 1))
    _make_health(db, f2.id, 85.0, datetime(2025, 12, 1))

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    data = resp.json()
    assert data["most_improved_field"] == "Campo Rising"


def test_treatments_applied_total(client, db):
    """treatments_applied_total aggregates across all fields."""
    farm = _make_farm(db)
    f1 = _make_field(db, farm.id, name="A")
    f2 = _make_field(db, farm.id, name="B")
    _make_treatment(db, f1.id, at=datetime(2025, 3, 1))
    _make_treatment(db, f1.id, at=datetime(2025, 4, 1))
    _make_treatment(db, f2.id, at=datetime(2025, 5, 1))

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    data = resp.json()
    assert data["treatments_applied_total"] == 3


def test_total_co2e_sequestered_aggregates(client, db):
    """total_co2e_sequestered_t sums carbon projection across fields with baselines."""
    farm = _make_farm(db)
    f1 = _make_field(db, farm.id, name="A")
    f2 = _make_field(db, farm.id, name="B")
    _make_carbon_baseline(db, f1.id, soc_percent=2.5)
    _make_carbon_baseline(db, f2.id, soc_percent=3.0)

    resp = client.get(f"/api/farms/{farm.id}/annual-report?year=2025")
    data = resp.json()
    assert data["total_co2e_sequestered_t"] > 0
