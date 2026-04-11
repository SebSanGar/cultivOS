"""Tests for GET /api/cooperatives/{cooperative_id}/portfolio-health endpoint."""

import pytest
from cultivos.db.models import (
    CarbonBaseline,
    Cooperative,
    Farm,
    Field,
    HealthScore,
    TreatmentRecord,
)
from datetime import datetime


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_coop(db, name="Cooperativa Test"):
    coop = Cooperative(name=name, state="Jalisco")
    db.add(coop)
    db.commit()
    return coop


def _make_farm(db, coop_id, name="Rancho Test", hectares=10.0):
    farm = Farm(name=name, state="Jalisco", cooperative_id=coop_id, total_hectares=hectares)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test", hectares=5.0):
    field = Field(farm_id=farm_id, name=name, crop_type="maiz", hectares=hectares)
    db.add(field)
    db.commit()
    return field


def _add_health(db, field_id, score, scored_at=None):
    hs = HealthScore(
        field_id=field_id,
        score=score,
        scored_at=scored_at or datetime.utcnow(),
    )
    db.add(hs)
    db.commit()
    return hs


def _add_treatment(db, field_id, organic=True):
    tr = TreatmentRecord(
        field_id=field_id,
        health_score_used=60.0,
        problema="test",
        causa_probable="test",
        tratamiento="compost",
        costo_estimado_mxn=0,
        urgencia="baja",
        prevencion="ninguna",
        organic=organic,
    )
    db.add(tr)
    db.commit()
    return tr


def _add_carbon_baseline(db, field_id, soc_percent=2.5):
    cb = CarbonBaseline(
        field_id=field_id,
        soc_percent=soc_percent,
        measurement_date="2026-01-01",
        lab_method="dry_combustion",
    )
    db.add(cb)
    db.commit()
    return cb


def _get_portfolio(client, coop_id):
    return client.get(f"/api/cooperatives/{coop_id}/portfolio-health")


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_cooperative(client):
    resp = _get_portfolio(client, 9999)
    assert resp.status_code == 404


def test_response_keys_present(client, db):
    coop = _make_coop(db)
    resp = _get_portfolio(client, coop.id)
    assert resp.status_code == 200
    data = resp.json()
    for key in ("cooperative_id", "name", "total_farms", "total_fields",
                "total_hectares", "avg_health_score", "fields_needing_attention",
                "total_co2e_sequestered", "economic_impact_mxn"):
        assert key in data, f"Missing key: {key}"


def test_empty_cooperative_returns_zeros(client, db):
    coop = _make_coop(db)
    resp = _get_portfolio(client, coop.id)
    data = resp.json()
    assert data["total_farms"] == 0
    assert data["total_fields"] == 0
    assert data["total_hectares"] == 0.0
    assert data["avg_health_score"] is None
    assert data["fields_needing_attention"] == 0
    assert data["total_co2e_sequestered"] == 0.0
    assert data["economic_impact_mxn"] == 0


def test_aggregates_across_two_farms(client, db):
    coop = _make_coop(db)
    farm1 = _make_farm(db, coop.id, "Farm 1", hectares=10.0)
    farm2 = _make_farm(db, coop.id, "Farm 2", hectares=5.0)
    field1 = _make_field(db, farm1.id, hectares=10.0)
    field2 = _make_field(db, farm2.id, hectares=5.0)
    _add_health(db, field1.id, 80)
    _add_health(db, field2.id, 60)

    resp = _get_portfolio(client, coop.id)
    data = resp.json()
    assert data["total_farms"] == 2
    assert data["total_fields"] == 2
    assert data["total_hectares"] == 15.0


def test_avg_health_score_computed(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id, hectares=20.0)
    field1 = _make_field(db, farm.id, "F1", hectares=10.0)
    field2 = _make_field(db, farm.id, "F2", hectares=10.0)
    _add_health(db, field1.id, 80)
    _add_health(db, field2.id, 60)

    resp = _get_portfolio(client, coop.id)
    data = resp.json()
    assert data["avg_health_score"] == pytest.approx(70.0, abs=1.0)


def test_fields_needing_attention_below_40(client, db):
    """Fields with latest health score < 40 counted as needing attention."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id, hectares=20.0)
    field1 = _make_field(db, farm.id, "Healthy", hectares=10.0)
    field2 = _make_field(db, farm.id, "Critical", hectares=10.0)
    _add_health(db, field1.id, 75)
    _add_health(db, field2.id, 30)  # critical

    resp = _get_portfolio(client, coop.id)
    data = resp.json()
    assert data["fields_needing_attention"] == 1


def test_total_co2e_sequestered_sums_carbon_baselines(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id, hectares=10.0)
    field1 = _make_field(db, farm.id, "F1", hectares=5.0)
    field2 = _make_field(db, farm.id, "F2", hectares=5.0)
    cb1 = _add_carbon_baseline(db, field1.id, soc_percent=2.0)
    cb2 = _add_carbon_baseline(db, field2.id, soc_percent=3.0)

    resp = _get_portfolio(client, coop.id)
    data = resp.json()
    assert data["total_co2e_sequestered"] > 0.0


def test_no_carbon_baselines_returns_zero_co2e(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id, hectares=10.0)
    _make_field(db, farm.id)

    resp = _get_portfolio(client, coop.id)
    data = resp.json()
    assert data["total_co2e_sequestered"] == 0.0


def test_economic_impact_positive_with_health_data(client, db):
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id, hectares=20.0)
    field = _make_field(db, farm.id, hectares=20.0)
    _add_health(db, field.id, 70)
    _add_treatment(db, field.id, organic=True)

    resp = _get_portfolio(client, coop.id)
    data = resp.json()
    assert data["economic_impact_mxn"] >= 0


def test_cooperative_name_returned(client, db):
    coop = _make_coop(db, name="Cooperativa Los Altos")
    resp = _get_portfolio(client, coop.id)
    data = resp.json()
    assert data["name"] == "Cooperativa Los Altos"
    assert data["cooperative_id"] == coop.id
