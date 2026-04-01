"""Farm report export endpoints (PDF and CSV)."""

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from sqlalchemy import func

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis, TreatmentRecord
from cultivos.db.session import get_db


def _safe_filename(name: str) -> str:
    """Sanitize a string for use in Content-Disposition filename."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(" ", "_"))[:50]
from cultivos.services.reports import generate_farm_export_csv, generate_farm_report_pdf

router = APIRouter(prefix="/api/farms/{farm_id}", tags=["reports"])


@router.post("/report")
def generate_farm_report(farm_id: int, db: Session = Depends(get_db)):
    """Generate and return a PDF health report for a farm."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm_data = {
        "name": farm.name,
        "owner_name": farm.owner_name,
        "municipality": farm.municipality,
        "state": farm.state,
        "total_hectares": farm.total_hectares,
    }

    fields_db = db.query(Field).filter(Field.farm_id == farm_id).all()
    fields_data = []
    treatments_data = []

    for field in fields_db:
        latest_hs = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        latest_ndvi = (
            db.query(NDVIResult)
            .filter(NDVIResult.field_id == field.id)
            .order_by(NDVIResult.analyzed_at.desc())
            .first()
        )

        fields_data.append({
            "name": field.name,
            "crop_type": field.crop_type,
            "hectares": field.hectares,
            "health_score": latest_hs.score if latest_hs else None,
            "health_trend": latest_hs.trend if latest_hs else None,
            "ndvi_mean": latest_ndvi.ndvi_mean if latest_ndvi else None,
        })

        # Get treatments for this field
        field_treatments = (
            db.query(TreatmentRecord)
            .filter(TreatmentRecord.field_id == field.id)
            .order_by(TreatmentRecord.created_at.desc())
            .all()
        )
        for tr in field_treatments:
            treatments_data.append({
                "field_name": field.name,
                "problema": tr.problema,
                "tratamiento": tr.tratamiento,
                "urgencia": tr.urgencia,
                "costo_estimado_mxn": tr.costo_estimado_mxn,
            })

    pdf_bytes = generate_farm_report_pdf(farm_data, fields_data, treatments_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="reporte_{_safe_filename(farm.name)}.pdf"',
        },
    )


@router.get("/export")
def export_farm_data(
    farm_id: int,
    format: str = Query(default="csv"),
    db: Session = Depends(get_db),
):
    """Export farm field data as CSV for FIRA loans and agronomist visits."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    fields_db = db.query(Field).filter(Field.farm_id == farm_id).all()
    fields_data = []

    for field in fields_db:
        latest_hs = (
            db.query(HealthScore)
            .filter(HealthScore.field_id == field.id)
            .order_by(HealthScore.scored_at.desc())
            .first()
        )
        latest_ndvi = (
            db.query(NDVIResult)
            .filter(NDVIResult.field_id == field.id)
            .order_by(NDVIResult.analyzed_at.desc())
            .first()
        )
        latest_soil = (
            db.query(SoilAnalysis)
            .filter(SoilAnalysis.field_id == field.id)
            .order_by(SoilAnalysis.sampled_at.desc())
            .first()
        )

        treatment_count = (
            db.query(func.count(TreatmentRecord.id))
            .filter(TreatmentRecord.field_id == field.id)
            .scalar()
        )
        last_treatment = (
            db.query(TreatmentRecord)
            .filter(TreatmentRecord.field_id == field.id)
            .order_by(TreatmentRecord.applied_at.desc())
            .first()
        )

        fields_data.append({
            "name": field.name,
            "crop_type": field.crop_type,
            "hectares": field.hectares,
            "health_score": latest_hs.score if latest_hs else None,
            "health_trend": latest_hs.trend if latest_hs else None,
            "ndvi_mean": latest_ndvi.ndvi_mean if latest_ndvi else None,
            "soil_ph": latest_soil.ph if latest_soil else None,
            "soil_organic_matter_pct": latest_soil.organic_matter_pct if latest_soil else None,
            "treatment_count": treatment_count,
            "last_treatment_date": last_treatment.applied_at if last_treatment and last_treatment.applied_at else None,
        })

    csv_content = generate_farm_export_csv(fields_data)
    safe_name = farm.name.replace(" ", "_")

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="export_{safe_name}.csv"',
        },
    )
