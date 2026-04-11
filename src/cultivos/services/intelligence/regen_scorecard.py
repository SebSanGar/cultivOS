"""Regenerative scorecard export service — computes per-field regen metrics for CSV export."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, SoilAnalysis, TreatmentRecord
from cultivos.services.intelligence.regenerative import compute_regenerative_score


def compute_farm_regen_scorecard_csv(
    farm_id: int,
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[dict]:
    """Compute per-field regenerative scorecard rows for a farm.

    Returns a list of dicts (one per field) ready for CSV serialization.
    Date range filters TreatmentRecord.created_at and SoilAnalysis.sampled_at.
    """
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        return None  # signals 404 to caller

    fields = db.query(Field).filter(Field.farm_id == farm_id).all()

    rows = []
    for field in fields:
        # --- Treatments in date range ---
        tq = db.query(TreatmentRecord).filter(TreatmentRecord.field_id == field.id)
        if date_from:
            from datetime import datetime
            tq = tq.filter(TreatmentRecord.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            from datetime import datetime
            tq = tq.filter(TreatmentRecord.created_at <= datetime.combine(date_to, datetime.max.time()))
        treatments = tq.all()

        total = len(treatments)
        organic_count = sum(1 for t in treatments if t.organic)
        organic_pct = round(organic_count / total * 100, 1) if total > 0 else 0.0
        synthetic_inputs_avoided = organic_count

        unique_methods = set()
        for t in treatments:
            if t.ancestral_method_name:
                unique_methods.add(t.ancestral_method_name)
            else:
                unique_methods.add(t.tratamiento[:30])
        if len(unique_methods) >= 3:
            biodiversity_score = 100.0
        elif len(unique_methods) == 2:
            biodiversity_score = 50.0
        elif len(unique_methods) == 1:
            biodiversity_score = 20.0
        else:
            biodiversity_score = 0.0

        # --- Soil organic carbon (latest in date range) ---
        sq = db.query(SoilAnalysis).filter(SoilAnalysis.field_id == field.id)
        if date_from:
            from datetime import datetime
            sq = sq.filter(SoilAnalysis.sampled_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            from datetime import datetime
            sq = sq.filter(SoilAnalysis.sampled_at <= datetime.combine(date_to, datetime.max.time()))
        latest_soil = sq.order_by(SoilAnalysis.sampled_at.desc()).first()
        soc_pct = latest_soil.organic_matter_pct if latest_soil and latest_soil.organic_matter_pct is not None else ""

        # --- Overall regen score (uses all data — representative summary) ---
        regen = compute_regenerative_score(field.id, db)
        regen_score = regen["score"]

        rows.append({
            "field_id": field.id,
            "field_name": field.name,
            "crop_type": field.crop_type or "",
            "hectares": field.hectares if field.hectares is not None else 0.0,
            "regen_score": regen_score,
            "organic_treatments_pct": organic_pct,
            "soc_pct": soc_pct,
            "synthetic_inputs_avoided": synthetic_inputs_avoided,
            "biodiversity_score": biodiversity_score,
            "date_from": str(date_from) if date_from else "",
            "date_to": str(date_to) if date_to else "",
        })

    return rows
