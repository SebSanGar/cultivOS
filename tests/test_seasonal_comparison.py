"""Tests for seasonal comparison endpoint."""

from datetime import datetime

import pytest

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


def _seed_farm_field(db):
    """Create a farm + field for testing."""
    farm = Farm(name="Test Farm", state="Jalisco")
    db.add(farm)
    db.flush()
    field = Field(
        farm_id=farm.id,
        name="Parcela A",
        crop_type="Maiz",
        hectares=10.0,
    )
    db.add(field)
    db.flush()
    return farm, field


def _add_health(db, field_id, score, ndvi_mean, scored_at):
    """Add a HealthScore record."""
    hs = HealthScore(
        field_id=field_id,
        score=score,
        ndvi_mean=ndvi_mean,
        trend="stable",
        sources=["ndvi"],
        breakdown={},
        scored_at=scored_at,
    )
    db.add(hs)
    db.flush()
    return hs


def _add_treatment(db, field_id, created_at):
    """Add a TreatmentRecord."""
    tr = TreatmentRecord(
        field_id=field_id,
        health_score_used=50.0,
        problema="Deficiencia",
        causa_probable="Bajo nitrogeno",
        tratamiento="Composta",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="Abono verde",
        organic=True,
        created_at=created_at,
    )
    db.add(tr)
    db.flush()
    return tr


# --- Test: both seasons have data ---

def test_seasonal_comparison_both_seasons(client, db):
    farm, field = _seed_farm_field(db)

    # Temporal (rainy) season records — July, August
    _add_health(db, field.id, 75.0, 0.65, datetime(2025, 7, 15))
    _add_health(db, field.id, 80.0, 0.70, datetime(2025, 8, 20))
    _add_treatment(db, field.id, datetime(2025, 7, 10))

    # Secas (dry) season records — January, March
    _add_health(db, field.id, 60.0, 0.50, datetime(2025, 1, 10))
    _add_health(db, field.id, 65.0, 0.55, datetime(2025, 3, 5))
    _add_treatment(db, field.id, datetime(2025, 2, 1))
    _add_treatment(db, field.id, datetime(2025, 3, 10))

    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
    assert resp.status_code == 200
    data = resp.json()

    temporal = data["temporal"]
    assert temporal["avg_health_score"] == pytest.approx(77.5, abs=0.1)
    assert temporal["avg_ndvi"] == pytest.approx(0.675, abs=0.01)
    assert temporal["treatment_count"] == 1
    assert temporal["data_points"] == 2

    secas = data["secas"]
    assert secas["avg_health_score"] == pytest.approx(62.5, abs=0.1)
    assert secas["avg_ndvi"] == pytest.approx(0.525, abs=0.01)
    assert secas["treatment_count"] == 2
    assert secas["data_points"] == 2


# --- Test: only one season has data ---

def test_seasonal_comparison_one_season_only(client, db):
    farm, field = _seed_farm_field(db)

    # Only temporal data
    _add_health(db, field.id, 70.0, 0.60, datetime(2025, 9, 1))
    _add_treatment(db, field.id, datetime(2025, 8, 15))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
    assert resp.status_code == 200
    data = resp.json()

    temporal = data["temporal"]
    assert temporal["avg_health_score"] == pytest.approx(70.0, abs=0.1)
    assert temporal["treatment_count"] == 1
    assert temporal["data_points"] == 1

    secas = data["secas"]
    assert secas["avg_health_score"] is None
    assert secas["avg_ndvi"] is None
    assert secas["treatment_count"] == 0
    assert secas["data_points"] == 0


# --- Test: no data at all ---

def test_seasonal_comparison_no_data(client, db):
    farm, field = _seed_farm_field(db)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/seasonal-comparison")
    assert resp.status_code == 200
    data = resp.json()

    for season in ("temporal", "secas"):
        assert data[season]["avg_health_score"] is None
        assert data[season]["avg_ndvi"] is None
        assert data[season]["treatment_count"] == 0
        assert data[season]["data_points"] == 0


# --- Test: field not found ---

def test_seasonal_comparison_field_not_found(client, db):
    farm = Farm(name="Test Farm", state="Jalisco")
    db.add(farm)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/fields/999/seasonal-comparison")
    assert resp.status_code == 404


# --- Pure service function tests ---

def test_compute_seasonal_comparison_pure():
    from cultivos.services.intelligence.seasonal_comparison import (
        compute_seasonal_comparison,
    )

    health_records = [
        {"score": 80.0, "ndvi_mean": 0.7, "scored_at": datetime(2025, 7, 1)},
        {"score": 60.0, "ndvi_mean": 0.5, "scored_at": datetime(2025, 1, 1)},
    ]
    treatments = [
        {"created_at": datetime(2025, 7, 5)},
        {"created_at": datetime(2025, 2, 10)},
        {"created_at": datetime(2025, 11, 20)},
    ]

    result = compute_seasonal_comparison(health_records, treatments)

    assert result["temporal"]["avg_health_score"] == pytest.approx(80.0)
    assert result["temporal"]["treatment_count"] == 1
    assert result["secas"]["avg_health_score"] == pytest.approx(60.0)
    assert result["secas"]["treatment_count"] == 2  # Jan + Nov are both secas


def test_compute_seasonal_comparison_empty():
    from cultivos.services.intelligence.seasonal_comparison import (
        compute_seasonal_comparison,
    )

    result = compute_seasonal_comparison([], [])
    assert result["temporal"]["data_points"] == 0
    assert result["secas"]["data_points"] == 0
