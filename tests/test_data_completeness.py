"""Tests for data completeness scoring per farm."""

from datetime import datetime

from cultivos.db.models import (
    Farm,
    Field,
    NDVIResult,
    SoilAnalysis,
    ThermalResult,
    TreatmentRecord,
    WeatherRecord,
)


def _seed_farm(db, name="Finca Test", n_fields=0):
    farm = Farm(name=name, owner_name="Test", total_hectares=10)
    db.add(farm)
    db.flush()
    fields = []
    for i in range(n_fields):
        f = Field(farm_id=farm.id, name=f"Campo {i+1}", crop_type="maiz", hectares=5)
        db.add(f)
        fields.append(f)
    db.flush()
    return farm, fields


# --- Pure service tests ---


def test_field_all_data_100_pct(db):
    """Field with all 5 data types = 100%."""
    from cultivos.services.intelligence.completeness import compute_data_completeness

    farm, [field] = _seed_farm(db, n_fields=1)
    db.add(SoilAnalysis(field_id=field.id, ph=6.5, sampled_at=datetime.utcnow()))
    db.add(NDVIResult(field_id=field.id, ndvi_mean=0.7, ndvi_std=0.1, ndvi_min=0.3, ndvi_max=0.9, pixels_total=1000, stress_pct=10, zones=[], analyzed_at=datetime.utcnow()))
    db.add(ThermalResult(field_id=field.id, temp_mean=28, temp_std=2, temp_min=22, temp_max=35, pixels_total=500, stress_pct=5, analyzed_at=datetime.utcnow()))
    db.add(TreatmentRecord(field_id=field.id, health_score_used=75.0, problema="test", causa_probable="test", tratamiento="compost", urgencia="baja", prevencion="rotacion", organic=True))
    db.add(WeatherRecord(farm_id=farm.id, temp_c=25, humidity_pct=60, wind_kmh=10, rainfall_mm=0, description="clear"))
    db.flush()

    result = compute_data_completeness(db, farm.id)
    assert result["farm_score"] == 100.0
    assert len(result["fields"]) == 1
    assert result["fields"][0]["score"] == 100.0
    assert result["fields"][0]["has_soil"] is True
    assert result["fields"][0]["has_ndvi"] is True
    assert result["fields"][0]["has_thermal"] is True
    assert result["fields"][0]["has_treatments"] is True
    assert result["fields"][0]["has_weather"] is True


def test_field_no_data_0_pct(db):
    """Field with zero data = 0%."""
    from cultivos.services.intelligence.completeness import compute_data_completeness

    farm, [field] = _seed_farm(db, n_fields=1)

    result = compute_data_completeness(db, farm.id)
    assert result["farm_score"] == 0.0
    assert result["fields"][0]["score"] == 0.0
    assert result["fields"][0]["has_soil"] is False
    assert result["fields"][0]["has_ndvi"] is False
    assert result["fields"][0]["has_thermal"] is False
    assert result["fields"][0]["has_treatments"] is False
    assert result["fields"][0]["has_weather"] is False


def test_farm_aggregate_averages_fields(db):
    """Farm score is average of field scores."""
    from cultivos.services.intelligence.completeness import compute_data_completeness

    farm, [f1, f2] = _seed_farm(db, n_fields=2)
    # f1 has soil + NDVI + weather = 3/5 = 60%
    db.add(SoilAnalysis(field_id=f1.id, ph=6.5, sampled_at=datetime.utcnow()))
    db.add(NDVIResult(field_id=f1.id, ndvi_mean=0.7, ndvi_std=0.1, ndvi_min=0.3, ndvi_max=0.9, pixels_total=1000, stress_pct=10, zones=[], analyzed_at=datetime.utcnow()))
    db.add(WeatherRecord(farm_id=farm.id, temp_c=25, humidity_pct=60, wind_kmh=10, rainfall_mm=0, description="clear"))
    # f2 has only weather = 1/5 = 20%
    db.flush()

    result = compute_data_completeness(db, farm.id)
    assert result["fields"][0]["score"] == 60.0  # f1
    assert result["fields"][1]["score"] == 20.0  # f2
    assert result["farm_score"] == 40.0  # average of 60 + 20


def test_empty_farm_zero(db):
    """Farm with no fields = 0%."""
    from cultivos.services.intelligence.completeness import compute_data_completeness

    farm, _ = _seed_farm(db, n_fields=0)

    result = compute_data_completeness(db, farm.id)
    assert result["farm_score"] == 0.0
    assert result["fields"] == []


def test_farm_not_found_raises(db):
    """Non-existent farm raises ValueError."""
    import pytest
    from cultivos.services.intelligence.completeness import compute_data_completeness

    with pytest.raises(ValueError, match="Farm 999 not found"):
        compute_data_completeness(db, 999)


# --- API route tests ---


def test_api_returns_200(client, db):
    farm, [field] = _seed_farm(db, n_fields=1)
    db.add(SoilAnalysis(field_id=field.id, ph=6.5, sampled_at=datetime.utcnow()))
    db.flush()

    resp = client.get(f"/api/farms/{farm.id}/data-completeness")
    assert resp.status_code == 200
    data = resp.json()
    assert "farm_score" in data
    assert "fields" in data
    assert data["fields"][0]["has_soil"] is True


def test_api_farm_not_found(client):
    resp = client.get("/api/farms/999/data-completeness")
    assert resp.status_code == 404
