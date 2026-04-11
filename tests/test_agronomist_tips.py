"""Tests for GET /api/knowledge/agronomist-tips endpoint."""

import pytest
from cultivos.db.models import AgronomistTip


def make_tip(db, crop="maiz", problem="drought", tip_text_es="Regar en la madrugada.", source="agronomist", region="jalisco", season="dry"):
    tip = AgronomistTip(
        crop=crop,
        problem=problem,
        tip_text_es=tip_text_es,
        source=source,
        region=region,
        season=season,
    )
    db.add(tip)
    db.commit()
    db.refresh(tip)
    return tip


def test_list_all_tips(client, db):
    """Returns all tips when no filters applied."""
    make_tip(db, crop="maiz", problem="drought")
    make_tip(db, crop="agave", problem="disease")
    resp = client.get("/api/knowledge/agronomist-tips")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_filter_by_crop(client, db):
    """Filters tips by crop param."""
    make_tip(db, crop="maiz", problem="drought")
    make_tip(db, crop="agave", problem="disease")
    make_tip(db, crop="maiz", problem="nutrient_deficiency")
    resp = client.get("/api/knowledge/agronomist-tips?crop=maiz")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(t["crop"] == "maiz" for t in data)


def test_filter_by_problem(client, db):
    """Filters tips by problem param."""
    make_tip(db, crop="maiz", problem="drought")
    make_tip(db, crop="agave", problem="drought")
    make_tip(db, crop="frijol", problem="disease")
    resp = client.get("/api/knowledge/agronomist-tips?problem=drought")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(t["problem"] == "drought" for t in data)


def test_filter_by_crop_and_problem(client, db):
    """Filters tips by both crop and problem."""
    make_tip(db, crop="maiz", problem="drought")
    make_tip(db, crop="maiz", problem="disease")
    make_tip(db, crop="agave", problem="drought")
    resp = client.get("/api/knowledge/agronomist-tips?crop=maiz&problem=drought")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["crop"] == "maiz"
    assert data[0]["problem"] == "drought"


def test_unknown_combo_returns_empty_not_404(client, db):
    """Unknown crop/problem combination returns empty list, not 404."""
    make_tip(db, crop="maiz", problem="drought")
    resp = client.get("/api/knowledge/agronomist-tips?crop=chia&problem=unknown")
    assert resp.status_code == 200
    assert resp.json() == []


def test_response_fields(client, db):
    """Response includes all expected fields."""
    make_tip(db, crop="maiz", problem="drought", tip_text_es="Mulchear el suelo.", source="CIMMYT", region="jalisco", season="dry")
    resp = client.get("/api/knowledge/agronomist-tips?crop=maiz")
    assert resp.status_code == 200
    tip = resp.json()[0]
    assert "id" in tip
    assert tip["crop"] == "maiz"
    assert tip["problem"] == "drought"
    assert tip["tip_text_es"] == "Mulchear el suelo."
    assert tip["source"] == "CIMMYT"
    assert tip["region"] == "jalisco"
    assert tip["season"] == "dry"


def test_empty_db_returns_empty_list(client, db):
    """Empty DB returns empty list, not error."""
    resp = client.get("/api/knowledge/agronomist-tips")
    assert resp.status_code == 200
    assert resp.json() == []
