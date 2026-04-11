"""Tests for regenerative scorecard CSV export — task #120.

GET /api/farms/{farm_id}/regen-scorecard/export.csv
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from cultivos.app import create_app
from cultivos.db.models import Farm, Field, SoilAnalysis, TreatmentRecord
from cultivos.db.session import get_db


EXPECTED_HEADERS = [
    "field_id", "field_name", "crop_type", "hectares",
    "regen_score", "organic_treatments_pct", "soc_pct",
    "synthetic_inputs_avoided", "biodiversity_score", "date_from", "date_to",
]


@pytest.fixture()
def client_empty(db):
    """Farm with no fields."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    farm = Farm(name="Rancho Vacio", state="Jalisco", total_hectares=0.0)
    db.add(farm)
    db.flush()
    db.refresh(farm)

    client = TestClient(app)
    client._farm_id = farm.id
    return client


@pytest.fixture()
def client_two_fields(db):
    """Farm with 2 fields, treatments, and soil data."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    farm = Farm(name="Rancho Dos Parcelas", state="Jalisco", total_hectares=10.0)
    db.add(farm)
    db.flush()
    db.refresh(farm)

    f1 = Field(name="Parcela Norte", farm_id=farm.id, crop_type="maiz", hectares=5.0)
    f2 = Field(name="Parcela Sur", farm_id=farm.id, crop_type="frijol", hectares=5.0)
    db.add_all([f1, f2])
    db.flush()
    db.refresh(f1)
    db.refresh(f2)

    # Treatments for field 1
    for i in range(3):
        db.add(TreatmentRecord(
            field_id=f1.id,
            health_score_used=60.0,
            problema="test",
            causa_probable="test",
            tratamiento=f"Tratamiento {i}",
            costo_estimado_mxn=1000,
            urgencia="media",
            prevencion="rotar",
            organic=(i < 2),  # 2 organic, 1 not
            created_at=datetime(2026, 3, 15),
        ))

    # Soil analysis for field 1
    db.add(SoilAnalysis(
        field_id=f1.id,
        organic_matter_pct=3.5,
        ph=6.5,
        sampled_at=datetime(2026, 3, 10),
    ))

    db.flush()
    client = TestClient(app)
    client._farm_id = farm.id
    client._field1_id = f1.id
    client._field2_id = f2.id
    return client


@pytest.fixture()
def client_date_filter(db):
    """Farm with treatments at two different dates — for date filter test."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    farm = Farm(name="Rancho Fechas", state="Jalisco", total_hectares=5.0)
    db.add(farm)
    db.flush()
    db.refresh(farm)

    field = Field(name="Parcela", farm_id=farm.id, crop_type="maiz", hectares=5.0)
    db.add(field)
    db.flush()
    db.refresh(field)

    # Treatment INSIDE date range (March 2026)
    db.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=60.0,
        problema="test",
        causa_probable="test",
        tratamiento="Composta",
        costo_estimado_mxn=1000,
        urgencia="media",
        prevencion="rotar",
        organic=True,
        created_at=datetime(2026, 3, 15),
    ))
    # Treatment OUTSIDE date range (January 2026)
    db.add(TreatmentRecord(
        field_id=field.id,
        health_score_used=50.0,
        problema="test",
        causa_probable="test",
        tratamiento="Fertilizante sintetico",
        costo_estimado_mxn=500,
        urgencia="media",
        prevencion="test",
        organic=False,
        created_at=datetime(2026, 1, 5),
    ))
    db.flush()

    client = TestClient(app)
    client._farm_id = farm.id
    client._field_id = field.id
    return client


def _parse_csv(text: str) -> tuple[list[str], list[dict]]:
    """Parse CSV text → (headers, rows)."""
    lines = [l for l in text.strip().splitlines() if l.strip()]
    headers = [h.strip() for h in lines[0].split(",")]
    rows = []
    for line in lines[1:]:
        values = [v.strip() for v in line.split(",")]
        rows.append(dict(zip(headers, values)))
    return headers, rows


# --- Test 1: CSV headers correct ---

def test_csv_headers_correct(client_two_fields):
    resp = client_two_fields.get(f"/api/farms/{client_two_fields._farm_id}/regen-scorecard/export.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    headers, _ = _parse_csv(resp.text)
    assert headers == EXPECTED_HEADERS


# --- Test 2: Rows match service output (one row per field) ---

def test_rows_match_field_count(client_two_fields):
    resp = client_two_fields.get(f"/api/farms/{client_two_fields._farm_id}/regen-scorecard/export.csv")
    assert resp.status_code == 200
    _, rows = _parse_csv(resp.text)
    assert len(rows) == 2  # two fields


def test_row_values_populated(client_two_fields):
    resp = client_two_fields.get(f"/api/farms/{client_two_fields._farm_id}/regen-scorecard/export.csv")
    assert resp.status_code == 200
    _, rows = _parse_csv(resp.text)
    # Find the row for Parcela Norte (has treatments + soil data)
    norte = next(r for r in rows if r["field_name"] == "Parcela Norte")
    assert norte["crop_type"] == "maiz"
    assert float(norte["hectares"]) == 5.0
    # 2 of 3 treatments are organic → 66.67%
    organic_pct = float(norte["organic_treatments_pct"])
    assert 60.0 < organic_pct < 70.0
    # soil data exists → soc_pct should be 3.5
    assert float(norte["soc_pct"]) == pytest.approx(3.5, abs=0.1)
    # 2 organic treatments avoided synthetic inputs
    assert int(norte["synthetic_inputs_avoided"]) == 2


# --- Test 3: Date filter honored ---

def test_date_filter_excludes_outside_range(client_date_filter):
    """Only the March treatment should count — January treatment is outside the filter."""
    resp = client_date_filter.get(
        f"/api/farms/{client_date_filter._farm_id}/regen-scorecard/export.csv",
        params={"date_from": "2026-03-01", "date_to": "2026-03-31"},
    )
    assert resp.status_code == 200
    _, rows = _parse_csv(resp.text)
    assert len(rows) == 1
    row = rows[0]
    # Only the organic March treatment is in range → 100% organic, 1 synthetic avoided
    assert float(row["organic_treatments_pct"]) == pytest.approx(100.0, abs=0.1)
    assert int(row["synthetic_inputs_avoided"]) == 1
    assert row["date_from"] == "2026-03-01"
    assert row["date_to"] == "2026-03-31"


# --- Test 4: Empty farm returns header-only CSV ---

def test_empty_farm_returns_header_only(client_empty):
    resp = client_empty.get(f"/api/farms/{client_empty._farm_id}/regen-scorecard/export.csv")
    assert resp.status_code == 200
    headers, rows = _parse_csv(resp.text)
    assert headers == EXPECTED_HEADERS
    assert rows == []


# --- Test 5: Unknown farm returns 404 ---

def test_unknown_farm_404(client_empty):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/farms/99999/regen-scorecard/export.csv")
    assert resp.status_code == 404
