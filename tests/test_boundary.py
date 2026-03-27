"""Tests for field boundary mapping — GPS polygons and area calculation."""

import pytest


# ── Unit tests for geo utility ──────────────────────────────────────

def test_calculate_area_hectares():
    """Polygon coordinates produce correct area in hectares."""
    from cultivos.utils.geo import calculate_polygon_area_hectares

    # ~1 km x 1 km square near Guadalajara (20.67°N, -103.35°W)
    # At 20.67°N latitude: 1° lon ≈ 104.5 km, 1° lat ≈ 110.6 km
    # 0.01° lon ≈ 1.045 km, 0.01° lat ≈ 1.106 km → ~1.16 km² ≈ 115.6 ha
    coords = [
        [-103.35, 20.67],
        [-103.34, 20.67],
        [-103.34, 20.68],
        [-103.35, 20.68],
    ]
    area = calculate_polygon_area_hectares(coords)
    # Should be approximately 115 hectares (allow 10% tolerance for Earth curvature)
    assert 100 < area < 130, f"Expected ~115 ha, got {area}"


def test_calculate_area_small_field():
    """Small field area calculated correctly."""
    from cultivos.utils.geo import calculate_polygon_area_hectares

    # Tiny triangle near Guadalajara
    coords = [
        [-103.35, 20.67],
        [-103.349, 20.67],
        [-103.3495, 20.671],
    ]
    area = calculate_polygon_area_hectares(coords)
    # Should be a small positive number
    assert 0 < area < 10, f"Expected small area, got {area}"


# ── API integration tests ───────────────────────────────────────────

def test_create_field_with_boundary(client, admin_headers):
    """POST field with coordinates array stores polygon and computes area."""
    # Create farm first
    farm = client.post("/api/farms", json={"name": "Finca Test"}, headers=admin_headers)
    farm_id = farm.json()["id"]

    # Create field with boundary
    coords = [
        [-103.35, 20.67],
        [-103.34, 20.67],
        [-103.34, 20.68],
        [-103.35, 20.68],
    ]
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Norte",
        "crop_type": "maiz",
        "boundary_coordinates": coords,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["boundary_coordinates"] == coords
    assert data["computed_area_hectares"] is not None
    assert data["computed_area_hectares"] > 100  # ~115 ha square


def test_boundary_validation(client, admin_headers):
    """Less than 3 points returns 422."""
    farm = client.post("/api/farms", json={"name": "Finca Validation"}, headers=admin_headers)
    farm_id = farm.json()["id"]

    # Only 2 points — should fail
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Mala",
        "boundary_coordinates": [[-103.35, 20.67], [-103.34, 20.67]],
    })
    assert resp.status_code == 422


def test_get_field_with_boundary(client, admin_headers):
    """GET field includes boundary coordinates and computed area."""
    farm = client.post("/api/farms", json={"name": "Finca Get"}, headers=admin_headers)
    farm_id = farm.json()["id"]

    coords = [
        [-103.35, 20.67],
        [-103.34, 20.67],
        [-103.34, 20.68],
        [-103.35, 20.68],
    ]
    create_resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Sur",
        "boundary_coordinates": coords,
    })
    field_id = create_resp.json()["id"]

    # GET the field
    resp = client.get(f"/api/farms/{farm_id}/fields/{field_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["boundary_coordinates"] == coords
    assert data["computed_area_hectares"] is not None
    assert data["computed_area_hectares"] > 0


def test_create_field_without_boundary(client, admin_headers):
    """Field without boundary still works — boundary and area are null."""
    farm = client.post("/api/farms", json={"name": "Finca NoBound"}, headers=admin_headers)
    farm_id = farm.json()["id"]

    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Simple",
        "crop_type": "frijol",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["boundary_coordinates"] is None
    assert data["computed_area_hectares"] is None
