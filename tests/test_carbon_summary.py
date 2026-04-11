"""Tests for GET /api/cooperatives/{coop_id}/carbon-summary endpoint."""

import pytest
from cultivos.db.models import CarbonBaseline, Cooperative, Farm, Field


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_coop(db, name="Cooperativa Carbon"):
    coop = Cooperative(name=name, state="Jalisco")
    db.add(coop)
    db.commit()
    return coop


def _make_farm(db, coop_id, name="Rancho Test"):
    farm = Farm(name=name, state="Jalisco", cooperative_id=coop_id, total_hectares=20.0)
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Test", hectares=5.0):
    field = Field(farm_id=farm_id, name=name, crop_type="maiz", hectares=hectares)
    db.add(field)
    db.commit()
    return field


def _add_carbon_baseline(db, field_id, soc_percent=2.5, lab_method="dry_combustion"):
    cb = CarbonBaseline(
        field_id=field_id,
        soc_percent=soc_percent,
        measurement_date="2026-01-01",
        lab_method=lab_method,
    )
    db.add(cb)
    db.commit()
    return cb


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_404_unknown_cooperative(client):
    r = client.get("/api/cooperatives/9999/carbon-summary")
    assert r.status_code == 404


def test_response_schema_keys(client, db):
    """Response contains all required schema keys."""
    coop = _make_coop(db)
    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    assert r.status_code == 200
    data = r.json()
    for key in ("cooperative_id", "total_co2e_baseline_t", "total_projected_5yr_t",
                "avg_confidence", "fields_with_data_count", "fields_total_count"):
        assert key in data, f"Missing key: {key}"


def test_empty_coop_no_farms(client, db):
    """Cooperative with no farms returns zero totals."""
    coop = _make_coop(db)
    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total_co2e_baseline_t"] == 0.0
    assert data["total_projected_5yr_t"] == 0.0
    assert data["fields_with_data_count"] == 0
    assert data["fields_total_count"] == 0


def test_cooperative_id_in_response(client, db):
    """cooperative_id is echoed back."""
    coop = _make_coop(db)
    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    assert r.json()["cooperative_id"] == coop.id


def test_two_farms_with_baselines_totals(client, db):
    """Two farms each with one field + baseline → totals add up."""
    coop = _make_coop(db)

    farm_a = _make_farm(db, coop.id, "Rancho A")
    farm_b = _make_farm(db, coop.id, "Rancho B")

    field_a = _make_field(db, farm_a.id, "Campo A", hectares=10.0)
    field_b = _make_field(db, farm_b.id, "Campo B", hectares=10.0)

    _add_carbon_baseline(db, field_a.id, soc_percent=2.0, lab_method="dry_combustion")
    _add_carbon_baseline(db, field_b.id, soc_percent=2.0, lab_method="dry_combustion")

    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["fields_with_data_count"] == 2
    assert data["fields_total_count"] == 2
    assert data["total_co2e_baseline_t"] > 0
    assert data["total_projected_5yr_t"] > data["total_co2e_baseline_t"]


def test_farm_without_baseline_excluded_from_data_count(client, db):
    """Farm with no baseline fields = fields counted in total but not in data count."""
    coop = _make_coop(db)

    farm_a = _make_farm(db, coop.id, "Con datos")
    farm_b = _make_farm(db, coop.id, "Sin datos")

    field_a = _make_field(db, farm_a.id, "Campo A", hectares=5.0)
    field_b = _make_field(db, farm_b.id, "Campo B", hectares=5.0)

    _add_carbon_baseline(db, field_a.id)

    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    assert r.status_code == 200
    data = r.json()
    assert data["fields_with_data_count"] == 1
    assert data["fields_total_count"] == 2


def test_avg_confidence_high_for_dry_combustion(client, db):
    """Fields with dry_combustion method → high confidence."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id, hectares=5.0)
    _add_carbon_baseline(db, field.id, lab_method="dry_combustion")

    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    assert r.json()["avg_confidence"] == "high"


def test_avg_confidence_medium_for_loi(client, db):
    """Fields with loss_on_ignition method → medium confidence."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    field = _make_field(db, farm.id, hectares=5.0)
    _add_carbon_baseline(db, field.id, lab_method="loss_on_ignition")

    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    assert r.json()["avg_confidence"] == "medium"


def test_no_baselines_returns_low_confidence(client, db):
    """Coop with fields but no baselines → low confidence."""
    coop = _make_coop(db)
    farm = _make_farm(db, coop.id)
    _make_field(db, farm.id)

    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    data = r.json()
    assert data["avg_confidence"] == "low"
    assert data["total_co2e_baseline_t"] == 0.0


def test_totals_are_additive(client, db):
    """Two 10-ha fields at same SOC → total = 2× single field."""
    coop = _make_coop(db)

    farm_a = _make_farm(db, coop.id, "A")
    farm_b = _make_farm(db, coop.id, "B")

    field_a = _make_field(db, farm_a.id, hectares=10.0)
    field_b = _make_field(db, farm_b.id, hectares=10.0)

    _add_carbon_baseline(db, field_a.id, soc_percent=3.0, lab_method="dry_combustion")
    _add_carbon_baseline(db, field_b.id, soc_percent=3.0, lab_method="dry_combustion")

    r = client.get(f"/api/cooperatives/{coop.id}/carbon-summary")
    data = r.json()

    # soc_t_per_ha = (3.0/100) * 0.30 * 1.3 * 10000 = 117 t C/ha
    # current_co2e per field = 117 * 10 ha * 3.67 = 4293.9 t CO2e
    # total for 2 identical fields = 8587.8
    assert abs(data["total_co2e_baseline_t"] - 8587.8) < 1.0
