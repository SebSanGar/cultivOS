"""Tests for farm data CSV export."""

import csv
import io
from datetime import datetime

import pytest

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis


@pytest.fixture
def farm_with_fields(db):
    """Create a farm with two fields and associated data."""
    farm = Farm(
        name="Rancho Prueba",
        owner_name="Juan Perez",
        municipality="Zapopan",
        state="Jalisco",
        total_hectares=50.0,
    )
    db.add(farm)
    db.flush()

    f1 = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=20.0)
    f2 = Field(farm_id=farm.id, name="Parcela Sur", crop_type="frijol", hectares=30.0)
    db.add_all([f1, f2])
    db.flush()

    # Health scores
    hs1 = HealthScore(
        field_id=f1.id, score=72.5, trend="improving",
        sources=["ndvi", "soil"], breakdown={"ndvi": 80, "soil": 60},
    )
    hs2 = HealthScore(
        field_id=f2.id, score=45.0, trend="declining",
        sources=["ndvi"], breakdown={"ndvi": 45},
    )
    db.add_all([hs1, hs2])

    # NDVI results
    ndvi1 = NDVIResult(
        field_id=f1.id, ndvi_mean=0.72, ndvi_std=0.08,
        ndvi_min=0.3, ndvi_max=0.9, pixels_total=1000,
        stress_pct=10.0, zones={},
    )
    db.add(ndvi1)

    # Soil
    soil1 = SoilAnalysis(
        field_id=f1.id, ph=6.5, organic_matter_pct=3.2,
        nitrogen_ppm=40.0, phosphorus_ppm=25.0, potassium_ppm=180.0,
        sampled_at=datetime(2026, 3, 1),
    )
    db.add(soil1)

    db.commit()
    return farm


def test_export_csv(client, admin_headers, farm_with_fields):
    """GET /api/farms/{id}/export?format=csv returns CSV with all fields + latest scores."""
    farm = farm_with_fields
    resp = client.get(f"/api/farms/{farm.id}/export?format=csv", headers=admin_headers)

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in resp.headers.get("content-disposition", "")

    # Parse CSV content
    text = resp.text
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    # Header + 2 field rows
    assert len(rows) == 3

    # Check field data is present
    field_names = {rows[1][0], rows[2][0]}
    assert "Parcela Norte" in field_names
    assert "Parcela Sur" in field_names


def test_export_spanish_headers(client, admin_headers, farm_with_fields):
    """Column headers must be in Spanish."""
    farm = farm_with_fields
    resp = client.get(f"/api/farms/{farm.id}/export?format=csv", headers=admin_headers)

    text = resp.text
    reader = csv.reader(io.StringIO(text))
    headers = next(reader)

    # Key headers in Spanish
    assert "Parcela" in headers
    assert "Cultivo" in headers
    assert "Hectareas" in headers
    assert "Salud" in headers
    assert "Tendencia" in headers
    assert "NDVI Promedio" in headers


def test_export_empty_farm(client, admin_headers, db):
    """Farm with no fields returns headers-only CSV."""
    farm = Farm(name="Granja Vacia", municipality="Tequila", state="Jalisco")
    db.add(farm)
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/export?format=csv", headers=admin_headers)

    assert resp.status_code == 200
    text = resp.text
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    # Only header row
    assert len(rows) == 1
    assert "Parcela" in rows[0]


def test_export_farm_not_found(client, admin_headers):
    """Export for nonexistent farm returns 404."""
    resp = client.get("/api/farms/9999/export?format=csv", headers=admin_headers)
    assert resp.status_code == 404
