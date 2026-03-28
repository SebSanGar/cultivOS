"""Tests for CSV export — treatment_count and last_treatment_date columns."""

import csv
import io
from datetime import datetime

from cultivos.db.models import (
    Farm, Field, HealthScore, NDVIResult, SoilAnalysis, TreatmentRecord,
)


def _seed_farm_with_treatments(db):
    """Create a farm with fields that have treatment data."""
    farm = Farm(name="Test Farm", state="Jalisco")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    f1 = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=10.5)
    f2 = Field(farm_id=farm.id, name="Parcela Sur", crop_type="agave", hectares=5.0)
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)

    # Field 1: health, NDVI, soil, 2 treatments
    db.add(HealthScore(field_id=f1.id, score=78.0, ndvi_mean=0.65, trend="improving", sources=["ndvi", "soil"]))
    db.add(NDVIResult(field_id=f1.id, ndvi_mean=0.65, ndvi_std=0.08, ndvi_min=0.3, ndvi_max=0.85, pixels_total=1000, stress_pct=12.0, zones=[]))
    db.add(SoilAnalysis(field_id=f1.id, ph=6.5, organic_matter_pct=3.2, sampled_at=datetime(2026, 3, 1)))
    db.add(TreatmentRecord(field_id=f1.id, health_score_used=78.0, problema="bajo NDVI", causa_probable="falta nutrientes", tratamiento="composta", costo_estimado_mxn=500, urgencia="media", prevencion="rotacion", organic=True, applied_at=datetime(2026, 3, 10)))
    db.add(TreatmentRecord(field_id=f1.id, health_score_used=78.0, problema="estres", causa_probable="sequia", tratamiento="riego", costo_estimado_mxn=200, urgencia="alta", prevencion="mulch", organic=True, applied_at=datetime(2026, 3, 15)))

    # Field 2: health only (no treatments)
    db.add(HealthScore(field_id=f2.id, score=55.0, ndvi_mean=0.45, trend="stable", sources=["ndvi"]))

    db.commit()
    return farm


def test_csv_export_has_treatment_columns(client, db, admin_headers):
    """CSV headers include Tratamientos and Ultimo Tratamiento."""
    farm = _seed_farm_with_treatments(db)
    resp = client.get(f"/api/farms/{farm.id}/export?format=csv", headers=admin_headers)

    assert resp.status_code == 200
    reader = csv.reader(io.StringIO(resp.text))
    headers = next(reader)
    assert "Tratamientos" in headers
    assert "Ultimo Tratamiento" in headers


def test_csv_export_treatment_count_correct(client, db, admin_headers):
    """Treatment count matches actual treatment records per field."""
    farm = _seed_farm_with_treatments(db)
    resp = client.get(f"/api/farms/{farm.id}/export?format=csv", headers=admin_headers)

    reader = csv.DictReader(io.StringIO(resp.text))
    rows = {r["Parcela"]: r for r in reader}

    assert int(rows["Parcela Norte"]["Tratamientos"]) == 2
    assert int(rows["Parcela Sur"]["Tratamientos"]) == 0


def test_csv_export_last_treatment_date_correct(client, db, admin_headers):
    """Last treatment date is the most recent applied_at date."""
    farm = _seed_farm_with_treatments(db)
    resp = client.get(f"/api/farms/{farm.id}/export?format=csv", headers=admin_headers)

    reader = csv.DictReader(io.StringIO(resp.text))
    rows = {r["Parcela"]: r for r in reader}

    assert rows["Parcela Norte"]["Ultimo Tratamiento"] == "2026-03-15"
    assert rows["Parcela Sur"]["Ultimo Tratamiento"] == ""


def test_csv_export_row_count_with_treatments(client, db, admin_headers):
    """CSV has correct number of rows (header + fields)."""
    farm = _seed_farm_with_treatments(db)
    resp = client.get(f"/api/farms/{farm.id}/export?format=csv", headers=admin_headers)

    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)
    assert len(rows) == 3  # header + 2 fields


def test_csv_export_farm_no_fields_has_treatment_headers(client, db, admin_headers):
    """Farm with no fields still includes treatment column headers."""
    farm = Farm(name="Empty Farm", state="Jalisco")
    db.add(farm)
    db.commit()
    db.refresh(farm)

    resp = client.get(f"/api/farms/{farm.id}/export?format=csv", headers=admin_headers)
    assert resp.status_code == 200

    reader = csv.reader(io.StringIO(resp.text))
    headers = next(reader)
    assert "Tratamientos" in headers
    assert "Ultimo Tratamiento" in headers
