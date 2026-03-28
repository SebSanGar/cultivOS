"""Thermal stress analysis endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/thermal."""

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, ThermalResult
from cultivos.db.session import get_db
from cultivos.models.thermal import ThermalResultCreate, ThermalResultOut
from cultivos.services.crop.thermal import compute_thermal_stress

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/thermal",
    tags=["thermal"],
)


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    """Validate farm and field exist and are linked."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.post("", response_model=ThermalResultOut, status_code=201)
def analyze_thermal(
    farm_id: int,
    field_id: int,
    body: ThermalResultCreate,
    db: Session = Depends(get_db),
):
    """Compute thermal stress from temperature array, store results."""
    _get_field(farm_id, field_id, db)

    thermal = np.array(body.thermal_band)

    if thermal.ndim != 2:
        raise HTTPException(status_code=422, detail="Thermal band must be 2-dimensional")
    if thermal.size == 0:
        raise HTTPException(status_code=422, detail="Thermal band must not be empty")

    stats = compute_thermal_stress(thermal)

    result = ThermalResult(
        field_id=field_id,
        flight_id=body.flight_id,
        temp_mean=stats["temp_mean"],
        temp_std=stats["temp_std"],
        temp_min=stats["temp_min"],
        temp_max=stats["temp_max"],
        pixels_total=stats["pixels_total"],
        stress_pct=stats["stress_pct"],
        irrigation_deficit=stats["irrigation_deficit"],
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.get("", response_model=list[ThermalResultOut])
def list_thermal_results(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """Return all thermal stress results for a field, ordered by most recent first."""
    _get_field(farm_id, field_id, db)
    return (
        db.query(ThermalResult)
        .filter(ThermalResult.field_id == field_id)
        .order_by(ThermalResult.analyzed_at.desc())
        .all()
    )


@router.get("/{thermal_id}", response_model=ThermalResultOut)
def get_thermal_result(
    farm_id: int,
    field_id: int,
    thermal_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a single thermal stress result by its ID for the given field."""
    _get_field(farm_id, field_id, db)
    result = (
        db.query(ThermalResult)
        .filter(ThermalResult.id == thermal_id, ThermalResult.field_id == field_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Thermal result not found")
    return result
