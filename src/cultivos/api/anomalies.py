"""Field-level anomaly detection — GET anomalies for a specific field."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult
from cultivos.db.session import get_db
from cultivos.models.anomaly import FieldAnomaliesOut
from cultivos.services.intelligence.anomaly import detect_health_anomalies, detect_ndvi_anomalies

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/anomalies",
    tags=["anomalies"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.get("", response_model=FieldAnomaliesOut)
def get_field_anomalies(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Detect health and NDVI anomalies for a single field.

    Health anomaly: score drops >15 points between consecutive readings.
    NDVI anomaly: latest NDVI mean drops >20% below historical average.
    """
    field = _get_field(farm_id, field_id, db)

    # Health anomalies
    health_records = (
        db.query(HealthScore)
        .filter(HealthScore.field_id == field.id)
        .order_by(HealthScore.scored_at.asc())
        .all()
    )
    health_anomalies = []
    if len(health_records) >= 2:
        score_dicts = [
            {"score": hs.score, "scored_at": hs.scored_at}
            for hs in health_records
        ]
        health_anomalies = detect_health_anomalies(score_dicts, field_name=field.name)

    # NDVI anomalies
    ndvi_records = (
        db.query(NDVIResult)
        .filter(NDVIResult.field_id == field.id)
        .order_by(NDVIResult.analyzed_at.asc())
        .all()
    )
    ndvi_anomalies = []
    if len(ndvi_records) >= 2:
        ndvi_dicts = [
            {"ndvi_mean": nr.ndvi_mean, "analyzed_at": nr.analyzed_at}
            for nr in ndvi_records
        ]
        ndvi_anomalies = detect_ndvi_anomalies(ndvi_dicts, field_name=field.name)

    return FieldAnomaliesOut(
        field_id=field.id,
        field_name=field.name,
        health_anomalies=health_anomalies,
        ndvi_anomalies=ndvi_anomalies,
    )
