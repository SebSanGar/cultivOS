"""Tests for batch field health assessment — POST /api/intel/batch-health."""

import os
import pytest
from datetime import datetime, timedelta


@pytest.fixture(autouse=True)
def enable_auth():
    os.environ["AUTH_ENABLED"] = "true"
    from cultivos.config import get_settings
    get_settings.cache_clear()
    yield
    os.environ.pop("AUTH_ENABLED", None)
    get_settings.cache_clear()


@pytest.fixture
def admin_token(client, db):
    # Admin users created directly in DB (admin self-registration blocked)
    from cultivos.db.models import User
    from cultivos.auth import hash_password
    # admin user created directly in DB


    if not db.query(User).filter(User.username == "batchadmin").first():
        db.add(User(username="batchadmin", hashed_password=hash_password("secret123"), role="admin"))
        db.commit()
    resp = client.post("/api/auth/login", json={
        "username": "batchadmin", "password": "secret123"
    })
    return resp.json()["access_token"]


@pytest.fixture
def admin_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def seed_fields(db):
    """Create 2 farms, 3 fields with NDVI data so health can be computed."""
    from cultivos.db.models import Farm, Field, NDVIResult, HealthScore

    farm1 = Farm(
        name="Rancho Uno", owner_name="Juan",
        location_lat=20.6, location_lon=-103.3,
        total_hectares=50, municipality="Zapopan",
        state="Jalisco", country="MX",
    )
    farm2 = Farm(
        name="Rancho Dos", owner_name="Pedro",
        location_lat=20.7, location_lon=-103.4,
        total_hectares=30, municipality="Tlajomulco",
        state="Jalisco", country="MX",
    )
    db.add_all([farm1, farm2])
    db.flush()

    f1 = Field(farm_id=farm1.id, name="Milpa Norte", crop_type="maiz", hectares=10)
    f2 = Field(farm_id=farm1.id, name="Agave Sur", crop_type="agave", hectares=15)
    f3 = Field(farm_id=farm2.id, name="Aguacate Este", crop_type="aguacate", hectares=8)
    db.add_all([f1, f2, f3])
    db.flush()

    # Add NDVI data for f1 and f3 (f2 has no data)
    now = datetime.utcnow()
    db.add(NDVIResult(
        field_id=f1.id, ndvi_mean=0.72, ndvi_std=0.05, ndvi_min=0.55,
        ndvi_max=0.85, pixels_total=10000, stress_pct=8.0, zones={},
        analyzed_at=now,
    ))
    db.add(NDVIResult(
        field_id=f3.id, ndvi_mean=0.65, ndvi_std=0.08, ndvi_min=0.40,
        ndvi_max=0.80, pixels_total=8000, stress_pct=15.0, zones={},
        analyzed_at=now,
    ))

    # Add a previous health score for f1 (for trend)
    db.add(HealthScore(
        field_id=f1.id, score=70.0, trend="stable",
        sources=["ndvi"], breakdown={"ndvi": 70.0},
        scored_at=now - timedelta(days=7),
    ))
    db.commit()

    return {"f1": f1.id, "f2": f2.id, "f3": f3.id}


def test_batch_health_valid_ids(client, admin_h, seed_fields):
    """Valid field IDs return health score + trend for each."""
    ids = [seed_fields["f1"], seed_fields["f3"]]
    resp = client.post("/api/intel/batch-health", json={"field_ids": ids}, headers=admin_h)
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) == 2

    # Both should have scores
    for entry in data["results"]:
        assert entry["field_id"] in ids
        assert entry["score"] is not None
        assert 0 <= entry["score"] <= 100
        assert entry["trend"] is not None


def test_batch_health_invalid_ids_return_null(client, admin_h, seed_fields):
    """Invalid IDs return null entries, not 404."""
    valid_id = seed_fields["f1"]
    invalid_id = 9999
    resp = client.post(
        "/api/intel/batch-health",
        json={"field_ids": [valid_id, invalid_id]},
        headers=admin_h,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2

    results_by_id = {r["field_id"]: r for r in data["results"]}

    # Valid field has score
    assert results_by_id[valid_id]["score"] is not None

    # Invalid field has null score
    assert results_by_id[invalid_id]["score"] is None
    assert results_by_id[invalid_id]["trend"] is None


def test_batch_health_empty_list(client, admin_h, seed_fields):
    """Empty list returns empty result."""
    resp = client.post("/api/intel/batch-health", json={"field_ids": []}, headers=admin_h)
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []


def test_batch_health_field_with_no_data(client, admin_h, seed_fields):
    """Field that exists but has no NDVI/soil/thermal/microbiome data returns null score."""
    no_data_id = seed_fields["f2"]
    resp = client.post(
        "/api/intel/batch-health",
        json={"field_ids": [no_data_id]},
        headers=admin_h,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["field_id"] == no_data_id
    assert data["results"][0]["score"] is None
