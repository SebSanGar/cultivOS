"""Tests for GET /api/intel/export — cross-farm CSV export for intel dashboard."""

import csv
import io
from datetime import datetime

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis, TreatmentRecord


def _seed_two_farms(db):
    """Create two farms with fields and mixed data coverage."""
    f1 = Farm(name="Granja Norte", state="Jalisco", municipality="Zapopan", total_hectares=25)
    f2 = Farm(name="Granja Sur", state="Jalisco", municipality="Tlaquepaque", total_hectares=10)
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)

    # Farm 1: 2 fields, full data
    p1 = Field(farm_id=f1.id, name="Parcela A", crop_type="maiz", hectares=15)
    p2 = Field(farm_id=f1.id, name="Parcela B", crop_type="agave", hectares=10)
    # Farm 2: 1 field, sparse data
    p3 = Field(farm_id=f2.id, name="Parcela C", crop_type="aguacate", hectares=10)
    db.add_all([p1, p2, p3])
    db.commit()
    db.refresh(p1)
    db.refresh(p2)
    db.refresh(p3)

    # Full data for p1
    db.add(HealthScore(field_id=p1.id, score=82.0, ndvi_mean=0.7, trend="improving", sources=["ndvi", "soil"]))
    db.add(NDVIResult(field_id=p1.id, ndvi_mean=0.7, ndvi_std=0.05, ndvi_min=0.4, ndvi_max=0.9, pixels_total=500, stress_pct=8.0, zones=[]))
    db.add(SoilAnalysis(field_id=p1.id, ph=6.8, organic_matter_pct=3.5, sampled_at=datetime(2026, 3, 1)))
    db.add(TreatmentRecord(field_id=p1.id, health_score_used=82.0, problema="bajo NDVI", causa_probable="nutrientes", tratamiento="composta", costo_estimado_mxn=500, urgencia="media", prevencion="rotacion", organic=True, applied_at=datetime(2026, 3, 10)))
    db.add(TreatmentRecord(field_id=p1.id, health_score_used=82.0, problema="estres", causa_probable="sequia", tratamiento="riego", costo_estimado_mxn=200, urgencia="alta", prevencion="mulch", organic=True, applied_at=datetime(2026, 3, 15)))

    # Partial data for p2
    db.add(HealthScore(field_id=p2.id, score=55.0, ndvi_mean=0.45, trend="stable", sources=["ndvi"]))

    # No data for p3 (sparse)

    db.commit()
    return f1, f2


def test_intel_export_returns_csv(client, db, admin_headers):
    """GET /api/intel/export returns CSV with correct content type."""
    _seed_two_farms(db)
    resp = client.get("/api/intel/export", headers=admin_headers)

    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment" in resp.headers.get("content-disposition", "")


def test_intel_export_has_farm_column(client, db, admin_headers):
    """CSV includes Granja column since this is cross-farm."""
    _seed_two_farms(db)
    resp = client.get("/api/intel/export", headers=admin_headers)

    reader = csv.reader(io.StringIO(resp.text))
    headers = next(reader)
    assert "Granja" in headers
    assert "Parcela" in headers


def test_intel_export_includes_all_fields(client, db, admin_headers):
    """CSV has one row per field across all farms."""
    _seed_two_farms(db)
    resp = client.get("/api/intel/export", headers=admin_headers)

    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)
    # header + 3 fields
    assert len(rows) == 4


def test_intel_export_field_data_correct(client, db, admin_headers):
    """Field with full data shows all columns populated."""
    _seed_two_farms(db)
    resp = client.get("/api/intel/export", headers=admin_headers)

    reader = csv.DictReader(io.StringIO(resp.text))
    rows = {r["Parcela"]: r for r in reader}

    assert rows["Parcela A"]["Granja"] == "Granja Norte"
    assert rows["Parcela A"]["Cultivo"] == "maiz"
    assert float(rows["Parcela A"]["Hectareas"]) == 15.0
    assert float(rows["Parcela A"]["Salud"]) == 82.0
    assert rows["Parcela A"]["Tendencia"] == "Mejorando"
    assert float(rows["Parcela A"]["NDVI Promedio"]) == 0.7
    assert float(rows["Parcela A"]["pH Suelo"]) == 6.8
    assert int(rows["Parcela A"]["Tratamientos"]) == 2


def test_intel_export_sparse_field_has_empty_cols(client, db, admin_headers):
    """Field with no health/soil/treatment data has empty values, not errors."""
    _seed_two_farms(db)
    resp = client.get("/api/intel/export", headers=admin_headers)

    reader = csv.DictReader(io.StringIO(resp.text))
    rows = {r["Parcela"]: r for r in reader}

    # Parcela C has no data at all
    assert rows["Parcela C"]["Granja"] == "Granja Sur"
    assert rows["Parcela C"]["Salud"] == ""
    assert rows["Parcela C"]["NDVI Promedio"] == ""
    assert rows["Parcela C"]["pH Suelo"] == ""
    assert int(rows["Parcela C"]["Tratamientos"]) == 0


def test_intel_export_empty_db(client, db, admin_headers):
    """Empty database returns CSV with headers only."""
    resp = client.get("/api/intel/export", headers=admin_headers)

    assert resp.status_code == 200
    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)
    assert len(rows) == 1  # header only
    assert "Granja" in rows[0]


def test_intel_export_accessible_without_auth(client, db):
    """Endpoint is accessible (auth dependency returns None when no token)."""
    resp = client.get("/api/intel/export")
    assert resp.status_code == 200
