"""Tests for field health heatmap data API — GET /api/farms/{id}/heatmap."""

from cultivos.db.models import Farm, Field, HealthScore
from cultivos.utils.geo import calculate_centroid


# ── Pure function tests ──────────────────────────────────────────────

SQUARE_BOUNDARY = [
    [-103.35, 20.65],
    [-103.34, 20.65],
    [-103.34, 20.66],
    [-103.35, 20.66],
]


def test_centroid_from_boundary():
    """Centroid should be the average lat/lon of boundary coordinates."""
    lat, lon = calculate_centroid(SQUARE_BOUNDARY)
    assert abs(lat - 20.655) < 0.001
    assert abs(lon - (-103.345)) < 0.001


def test_centroid_triangle():
    """Centroid of a triangle."""
    coords = [[-100.0, 20.0], [-100.0, 21.0], [-99.0, 20.0]]
    lat, lon = calculate_centroid(coords)
    # Average: lat=(20+21+20)/3=20.333, lon=(-100+-100+-99)/3=-99.667
    assert abs(lat - 20.333) < 0.01
    assert abs(lon - (-99.667)) < 0.01


def test_centroid_empty_returns_none():
    """Empty coordinate list returns None."""
    assert calculate_centroid([]) is None


def test_centroid_none_returns_none():
    """None input returns None."""
    assert calculate_centroid(None) is None


# ── API endpoint tests ───────────────────────────────────────────────

def _create_farm_with_fields(db, with_boundary=True, with_health=True):
    """Helper: create a farm with 2 fields, optionally with boundaries and health scores."""
    farm = Farm(name="Test Farm", state="Jalisco", country="MX")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    boundary = SQUARE_BOUNDARY if with_boundary else None
    field1 = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz",
                   boundary_coordinates=boundary)
    field2 = Field(farm_id=farm.id, name="Parcela B", crop_type="agave",
                   boundary_coordinates=None)  # always no boundary for second field
    db.add_all([field1, field2])
    db.commit()
    db.refresh(field1)
    db.refresh(field2)

    if with_health:
        hs = HealthScore(field_id=field1.id, score=78.5, trend="improving",
                         sources=["ndvi", "soil"])
        db.add(hs)
        db.commit()

    return farm


def test_heatmap_returns_all_fields(client, db, admin_headers):
    """Heatmap endpoint returns data for every field in the farm."""
    farm = _create_farm_with_fields(db)
    resp = client.get(f"/api/farms/{farm.id}/heatmap", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["farm_id"] == farm.id
    assert len(data["fields"]) == 2


def test_heatmap_centroid_from_boundary(client, db, admin_headers):
    """Field with boundary_coordinates has a computed centroid."""
    farm = _create_farm_with_fields(db)
    resp = client.get(f"/api/farms/{farm.id}/heatmap", headers=admin_headers)
    fields = resp.json()["fields"]
    # Parcela A has boundary
    parcela_a = next(f for f in fields if f["field_name"] == "Parcela A")
    assert parcela_a["centroid_lat"] is not None
    assert parcela_a["centroid_lon"] is not None
    assert abs(parcela_a["centroid_lat"] - 20.655) < 0.001
    assert abs(parcela_a["centroid_lon"] - (-103.345)) < 0.001


def test_heatmap_null_centroid_no_boundary(client, db, admin_headers):
    """Field without boundary_coordinates has null centroid."""
    farm = _create_farm_with_fields(db)
    resp = client.get(f"/api/farms/{farm.id}/heatmap", headers=admin_headers)
    fields = resp.json()["fields"]
    parcela_b = next(f for f in fields if f["field_name"] == "Parcela B")
    assert parcela_b["centroid_lat"] is None
    assert parcela_b["centroid_lon"] is None


def test_heatmap_includes_health_score(client, db, admin_headers):
    """Field with health score returns latest score and trend."""
    farm = _create_farm_with_fields(db, with_health=True)
    resp = client.get(f"/api/farms/{farm.id}/heatmap", headers=admin_headers)
    fields = resp.json()["fields"]
    parcela_a = next(f for f in fields if f["field_name"] == "Parcela A")
    assert parcela_a["health_score"] == 78.5
    assert parcela_a["health_trend"] == "improving"


def test_heatmap_null_health_when_no_scores(client, db, admin_headers):
    """Field without health scores returns null score and trend."""
    farm = _create_farm_with_fields(db, with_health=False)
    resp = client.get(f"/api/farms/{farm.id}/heatmap", headers=admin_headers)
    fields = resp.json()["fields"]
    for f in fields:
        assert f["health_score"] is None
        assert f["health_trend"] is None


def test_heatmap_404_missing_farm(client, admin_headers):
    """Requesting heatmap for non-existent farm returns 404."""
    resp = client.get("/api/farms/9999/heatmap", headers=admin_headers)
    assert resp.status_code == 404


def test_heatmap_empty_farm_no_fields(client, db, admin_headers):
    """Farm with no fields returns empty fields list."""
    farm = Farm(name="Empty Farm", state="Jalisco", country="MX")
    db.add(farm)
    db.commit()
    db.refresh(farm)
    resp = client.get(f"/api/farms/{farm.id}/heatmap", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["fields"] == []
