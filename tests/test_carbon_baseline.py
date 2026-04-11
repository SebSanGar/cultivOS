"""Tests for soil carbon baseline (POST) and projection (GET) endpoints."""

import pytest
from cultivos.db.models import Farm, Field


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_farm(db, name="Rancho Carbon"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name="Campo Sur", hectares=5.0):
    field = Field(farm_id=farm_id, name=name, crop_type="maiz", hectares=hectares)
    db.add(field)
    db.commit()
    return field


def _post_baseline(client, farm_id, field_id, soc_percent=2.5, measurement_date="2026-01-15", lab_method="dry_combustion"):
    return client.post(
        f"/api/farms/{farm_id}/fields/{field_id}/carbon-baseline",
        json={"soc_percent": soc_percent, "measurement_date": measurement_date, "lab_method": lab_method},
    )


# ── POST /carbon-baseline tests ───────────────────────────────────────────────

def test_post_baseline_200(client, db):
    """POST returns 200 and baseline is stored."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    resp = _post_baseline(client, farm.id, field.id)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["field_id"] == field.id
    assert data["soc_percent"] == 2.5
    assert data["measurement_date"] == "2026-01-15"
    assert data["lab_method"] == "dry_combustion"
    assert "id" in data


def test_post_baseline_stored_in_db(client, db):
    """Baseline is persisted and retrievable via GET projection."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _post_baseline(client, farm.id, field.id, soc_percent=1.8)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection")
    assert resp.status_code == 200
    assert resp.json()["baseline_soc_pct"] == 1.8


def test_post_baseline_404_unknown_farm(client):
    """POST to unknown farm → 404."""
    resp = client.post(
        "/api/farms/99999/fields/1/carbon-baseline",
        json={"soc_percent": 2.0, "measurement_date": "2026-01-01", "lab_method": "dry_combustion"},
    )
    assert resp.status_code == 404


def test_post_baseline_404_unknown_field(client, db):
    """POST to unknown field → 404."""
    farm = _make_farm(db)
    resp = client.post(
        f"/api/farms/{farm.id}/fields/99999/carbon-baseline",
        json={"soc_percent": 2.0, "measurement_date": "2026-01-01", "lab_method": "dry_combustion"},
    )
    assert resp.status_code == 404


# ── GET /carbon-projection tests ──────────────────────────────────────────────

def test_get_projection_response_keys(client, db):
    """GET projection returns all required keys."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, hectares=10.0)
    _post_baseline(client, farm.id, field.id)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for key in ["field_id", "baseline_soc_pct", "hectares", "current_co2e_t",
                "projected_5yr_co2e_t", "sequestration_rate_t_per_yr", "confidence"]:
        assert key in data, f"Missing key: {key}"


def test_get_projection_math_3_67_ratio(client, db):
    """Projection uses 3.67 CO2:C ratio correctly."""
    farm = _make_farm(db)
    # Field with 10 ha, SOC = 2.0%
    # soc_t/ha = 2.0/100 * 1.3 * 0.3 * 10000 = 78.0
    # current_co2e_t = 78.0 * 10 * 3.67 = 2862.6
    field = _make_field(db, farm.id, hectares=10.0)
    _post_baseline(client, farm.id, field.id, soc_percent=2.0, lab_method="dry_combustion")

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection")
    data = resp.json()
    assert abs(data["current_co2e_t"] - 2862.6) < 0.5, f"Expected ~2862.6, got {data['current_co2e_t']}"


def test_get_projection_5yr_includes_sequestration(client, db):
    """5-year projection = current + sequestration_rate * 5."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, hectares=5.0)
    _post_baseline(client, farm.id, field.id, soc_percent=2.0)

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection")
    data = resp.json()
    expected_5yr = round(data["current_co2e_t"] + data["sequestration_rate_t_per_yr"] * 5, 2)
    assert abs(data["projected_5yr_co2e_t"] - expected_5yr) < 0.01


def test_get_projection_multiple_baselines_uses_latest(client, db):
    """When multiple baselines exist, projection uses the most recent one."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, hectares=4.0)
    # Post two baselines — the second (higher SOC) should win
    _post_baseline(client, farm.id, field.id, soc_percent=1.0, measurement_date="2025-06-01")
    _post_baseline(client, farm.id, field.id, soc_percent=3.0, measurement_date="2026-03-01")

    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection")
    assert resp.status_code == 200
    assert resp.json()["baseline_soc_pct"] == 3.0


def test_get_projection_confidence_dry_combustion(client, db):
    """dry_combustion lab method → confidence = high."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _post_baseline(client, farm.id, field.id, lab_method="dry_combustion")
    data = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection").json()
    assert data["confidence"] == "high"


def test_get_projection_confidence_loss_on_ignition(client, db):
    """loss_on_ignition → confidence = medium."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _post_baseline(client, farm.id, field.id, lab_method="loss_on_ignition")
    data = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection").json()
    assert data["confidence"] == "medium"


def test_get_projection_confidence_unknown_method(client, db):
    """Unknown lab method → confidence = low."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    _post_baseline(client, farm.id, field.id, lab_method="visual_estimate")
    data = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection").json()
    assert data["confidence"] == "low"


def test_get_projection_no_baseline_404(client, db):
    """No baseline recorded → 404 with informative message."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id)
    resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/carbon-projection")
    assert resp.status_code == 404


def test_get_projection_404_unknown_farm(client):
    """Unknown farm → 404."""
    resp = client.get("/api/farms/99999/fields/1/carbon-projection")
    assert resp.status_code == 404
