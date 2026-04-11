"""Tests for GET /api/farms/{farm_id}/field-priority — ranked field urgency."""

import pytest
from cultivos.db.models import Farm, Field, HealthScore


def _make_farm(db, name="Rancho Test"):
    farm = Farm(name=name, state="Jalisco")
    db.add(farm)
    db.commit()
    return farm


def _make_field(db, farm_id, name, crop_type="maiz", hectares=5.0):
    field = Field(farm_id=farm_id, name=name, crop_type=crop_type, hectares=hectares)
    db.add(field)
    db.commit()
    return field


def _seed_health(db, field_id, score):
    hs = HealthScore(field_id=field_id, score=score, sources=["health"], breakdown={})
    db.add(hs)
    db.commit()
    return hs


def test_response_keys_present(client, db):
    """GET /api/farms/{id}/field-priority returns expected schema."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, "Campo Uno")
    _seed_health(db, field.id, score=60.0)

    resp = client.get(f"/api/farms/{farm.id}/field-priority")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "farm_id" in data
    assert "fields" in data
    assert len(data["fields"]) == 1
    item = data["fields"][0]
    assert "field_id" in item
    assert "name" in item
    assert "crop_type" in item
    assert "priority_score" in item
    assert "top_issue" in item
    assert "recommended_action" in item


def test_fields_sorted_by_priority_desc(client, db):
    """Field with worse health (lower score) gets higher priority (higher score)."""
    farm = _make_farm(db)
    field_good = _make_field(db, farm.id, "Campo Sano")
    field_bad = _make_field(db, farm.id, "Campo Critico")

    _seed_health(db, field_good.id, score=80.0)   # low stress (20)
    _seed_health(db, field_bad.id, score=30.0)    # high stress (70)

    resp = client.get(f"/api/farms/{farm.id}/field-priority")
    assert resp.status_code == 200
    data = resp.json()
    fields = data["fields"]
    assert len(fields) == 2
    # Campo Critico should be first (higher priority score)
    assert fields[0]["name"] == "Campo Critico"
    assert fields[0]["priority_score"] > fields[1]["priority_score"]


def test_farm_no_fields_empty_list(client, db):
    """Farm with no fields returns empty fields list."""
    farm = _make_farm(db)

    resp = client.get(f"/api/farms/{farm.id}/field-priority")
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert data["fields"] == []


def test_404_unknown_farm(client):
    """Unknown farm_id returns 404."""
    resp = client.get("/api/farms/99999/field-priority")
    assert resp.status_code == 404


def test_top_issue_and_action_present(client, db):
    """Each field entry has non-empty top_issue and recommended_action strings."""
    farm = _make_farm(db)
    field = _make_field(db, farm.id, "Campo Centro")
    _seed_health(db, field.id, score=40.0)  # medium/high stress

    resp = client.get(f"/api/farms/{farm.id}/field-priority")
    assert resp.status_code == 200
    item = resp.json()["fields"][0]
    assert isinstance(item["top_issue"], str) and len(item["top_issue"]) > 0
    assert isinstance(item["recommended_action"], str) and len(item["recommended_action"]) > 0
