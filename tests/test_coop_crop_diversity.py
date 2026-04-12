"""Tests for cooperative crop diversity score.

GET /api/cooperatives/{coop_id}/crop-diversity
Composes Farm + Field ORM to compute distinct crops, Shannon diversity index,
and top 3 crops by hectares across a cooperative.
"""

import math

import pytest


@pytest.fixture
def coop(db):
    from cultivos.db.models import Cooperative
    c = Cooperative(name="Cooperativa Diversidad", state="Jalisco")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _farm(db, coop, name="Rancho"):
    from cultivos.db.models import Farm
    f = Farm(name=name, state="Jalisco", total_hectares=50.0, cooperative_id=coop.id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _field(db, farm, crop_type, hectares=5.0, name="Parcela"):
    from cultivos.db.models import Field
    fld = Field(farm_id=farm.id, name=name, crop_type=crop_type, hectares=hectares)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def test_crop_diversity_single_crop(client, db, coop):
    farm = _farm(db, coop, name="Rancho Solo")
    _field(db, farm, "maiz", 10.0, name="p1")
    _field(db, farm, "maiz", 5.0, name="p2")

    resp = client.get(f"/api/cooperatives/{coop.id}/crop-diversity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["total_farms"] == 1
    assert data["total_fields"] == 2
    assert data["distinct_crops_coop"] == 1
    assert data["shannon_index"] == 0.0
    assert len(data["top_crops"]) == 1
    assert data["top_crops"][0]["crop_type"] == "maiz"
    assert data["top_crops"][0]["hectares"] == 15.0
    assert data["top_crops"][0]["pct"] == 100.0
    assert len(data["farms"]) == 1
    assert data["farms"][0]["distinct_crops"] == 1
    assert data["farms"][0]["crop_types"] == ["maiz"]


def test_crop_diversity_multiple(client, db, coop):
    f1 = _farm(db, coop, name="Rancho A")
    f2 = _farm(db, coop, name="Rancho B")
    _field(db, f1, "maiz", 10.0, name="m1")
    _field(db, f1, "frijol", 4.0, name="fb1")
    _field(db, f2, "calabaza", 6.0, name="c1")
    _field(db, f2, "maiz", 5.0, name="m2")

    resp = client.get(f"/api/cooperatives/{coop.id}/crop-diversity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_farms"] == 2
    assert data["total_fields"] == 4
    assert data["distinct_crops_coop"] == 3

    farms_by_name = {f["farm_name"]: f for f in data["farms"]}
    assert farms_by_name["Rancho A"]["distinct_crops"] == 2
    assert sorted(farms_by_name["Rancho A"]["crop_types"]) == ["frijol", "maiz"]
    assert farms_by_name["Rancho B"]["distinct_crops"] == 2
    assert sorted(farms_by_name["Rancho B"]["crop_types"]) == ["calabaza", "maiz"]


def test_crop_diversity_shannon_index(client, db, coop):
    # Equal 50/50 split of two crops → H = ln(2) ≈ 0.6931
    farm = _farm(db, coop, name="Rancho Shannon")
    _field(db, farm, "maiz", 10.0, name="m1")
    _field(db, farm, "frijol", 10.0, name="fb1")

    resp = client.get(f"/api/cooperatives/{coop.id}/crop-diversity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["distinct_crops_coop"] == 2
    assert data["shannon_index"] == pytest.approx(math.log(2), abs=1e-4)


def test_crop_diversity_top3(client, db, coop):
    # 5 distinct crops — top_crops must list only the top 3 by hectares
    f1 = _farm(db, coop, name="Rancho Top")
    _field(db, f1, "maiz", 20.0, name="A")
    _field(db, f1, "aguacate", 15.0, name="B")
    _field(db, f1, "frijol", 10.0, name="C")
    _field(db, f1, "agave", 5.0, name="D")
    _field(db, f1, "calabaza", 2.0, name="E")

    resp = client.get(f"/api/cooperatives/{coop.id}/crop-diversity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["distinct_crops_coop"] == 5
    assert len(data["top_crops"]) == 3
    top_names = [c["crop_type"] for c in data["top_crops"]]
    assert top_names == ["maiz", "aguacate", "frijol"]
    # Hectares DESC, pct computed against total 52
    assert data["top_crops"][0]["hectares"] == 20.0
    assert data["top_crops"][0]["pct"] == pytest.approx(20.0 / 52.0 * 100.0, abs=0.01)


def test_crop_diversity_empty_coop(client, db, coop):
    resp = client.get(f"/api/cooperatives/{coop.id}/crop-diversity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["total_farms"] == 0
    assert data["total_fields"] == 0
    assert data["distinct_crops_coop"] == 0
    assert data["shannon_index"] == 0.0
    assert data["top_crops"] == []
    assert data["farms"] == []


def test_crop_diversity_404(client):
    resp = client.get("/api/cooperatives/99999/crop-diversity")
    assert resp.status_code == 404
