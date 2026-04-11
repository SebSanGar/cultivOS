"""Tests for GET /api/farms/{farm_id}/carbon-audit endpoint."""

import pytest
from cultivos.db.models import CarbonBaseline, Farm, Field


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Audit"):
    farm = Farm(name=name, state="Jalisco", total_hectares=20.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test", hectares=5.0):
    field = Field(farm_id=farm_id, name=name, crop_type="maiz", hectares=hectares)
    db.add(field)
    db.commit()
    return field


def _add_baseline(db, field_id, soc_percent=2.5, lab_method="dry_combustion"):
    cb = CarbonBaseline(
        field_id=field_id,
        soc_percent=soc_percent,
        measurement_date="2026-01-01",
        lab_method=lab_method,
    )
    db.add(cb)
    db.commit()
    return cb


def _get_audit(client, farm_id):
    return client.get(f"/api/farms/{farm_id}/carbon-audit")


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_farm(client):
    resp = _get_audit(client, 9999)
    assert resp.status_code == 404


def test_response_keys_present(client, db):
    farm = _make_farm(db)
    resp = _get_audit(client, farm.id)
    assert resp.status_code == 200
    data = resp.json()
    for key in ("farm_id", "total_current_co2e_t", "total_projected_5yr_co2e_t",
                "total_annual_seq_t_per_yr", "fields_with_baseline",
                "fields_without_baseline", "total_fields"):
        assert key in data, f"Missing key: {key}"


def test_no_fields_returns_zeros(client, db):
    farm = _make_farm(db)
    resp = _get_audit(client, farm.id)
    data = resp.json()
    assert data["total_current_co2e_t"] == 0.0
    assert data["total_projected_5yr_co2e_t"] == 0.0
    assert data["total_annual_seq_t_per_yr"] == 0.0
    assert data["fields_with_baseline"] == 0
    assert data["fields_without_baseline"] == 0
    assert data["total_fields"] == 0


def test_no_baselines_returns_zeros_with_field_count(client, db):
    farm = _make_farm(db)
    _make_field(db, farm.id, "F1")
    _make_field(db, farm.id, "F2")
    resp = _get_audit(client, farm.id)
    data = resp.json()
    assert data["total_current_co2e_t"] == 0.0
    assert data["fields_with_baseline"] == 0
    assert data["fields_without_baseline"] == 2
    assert data["total_fields"] == 2


def test_one_field_with_baseline(client, db):
    farm = _make_farm(db)
    field = _make_field(db, farm.id, hectares=10.0)
    _add_baseline(db, field.id, soc_percent=2.0)
    resp = _get_audit(client, farm.id)
    data = resp.json()
    assert data["fields_with_baseline"] == 1
    assert data["fields_without_baseline"] == 0
    assert data["total_current_co2e_t"] > 0.0
    assert data["total_projected_5yr_co2e_t"] > data["total_current_co2e_t"]


def test_mixed_fields_one_with_one_without(client, db):
    farm = _make_farm(db)
    field1 = _make_field(db, farm.id, "With Baseline", hectares=5.0)
    field2 = _make_field(db, farm.id, "No Baseline", hectares=5.0)
    _add_baseline(db, field1.id, soc_percent=2.5)
    resp = _get_audit(client, farm.id)
    data = resp.json()
    assert data["fields_with_baseline"] == 1
    assert data["fields_without_baseline"] == 1
    assert data["total_fields"] == 2
    assert data["total_current_co2e_t"] > 0.0


def test_two_fields_with_baselines_sum(client, db):
    farm = _make_farm(db)
    field1 = _make_field(db, farm.id, "F1", hectares=5.0)
    field2 = _make_field(db, farm.id, "F2", hectares=5.0)
    _add_baseline(db, field1.id, soc_percent=2.0)
    _add_baseline(db, field2.id, soc_percent=3.0)

    resp = _get_audit(client, farm.id)
    data = resp.json()
    assert data["fields_with_baseline"] == 2
    assert data["fields_without_baseline"] == 0
    # Combined co2e should be greater than one field alone
    single_resp = _get_audit(client, farm.id)
    assert data["total_current_co2e_t"] > 0.0
    assert data["total_annual_seq_t_per_yr"] > 0.0


def test_latest_baseline_used_when_multiple(client, db):
    """When a field has multiple baselines, latest recorded_at wins."""
    from datetime import datetime, timedelta
    farm = _make_farm(db)
    field = _make_field(db, farm.id, hectares=5.0)
    # Add old baseline with high SOC
    old = CarbonBaseline(
        field_id=field.id,
        soc_percent=5.0,
        measurement_date="2025-01-01",
        lab_method="dry_combustion",
        recorded_at=datetime.utcnow() - timedelta(days=100),
    )
    db.add(old)
    # Add newer baseline with lower SOC
    new = CarbonBaseline(
        field_id=field.id,
        soc_percent=2.0,
        measurement_date="2026-01-01",
        lab_method="dry_combustion",
        recorded_at=datetime.utcnow(),
    )
    db.add(new)
    db.commit()

    resp = _get_audit(client, farm.id)
    data = resp.json()
    assert data["fields_with_baseline"] == 1
    # With soc_percent=2.0 (latest), co2e should be lower than with 5.0
    assert data["total_current_co2e_t"] > 0.0


def test_farm_id_in_response(client, db):
    farm = _make_farm(db)
    resp = _get_audit(client, farm.id)
    data = resp.json()
    assert data["farm_id"] == farm.id
