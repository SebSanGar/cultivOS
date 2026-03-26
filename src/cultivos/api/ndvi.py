"""NDVI analysis endpoints — nested under /api/farms/{farm_id}/fields/{field_id}/ndvi."""

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, NDVIResult
from cultivos.db.session import get_db
from cultivos.models.ndvi import NDVIResultCreate, NDVIResultOut
from cultivos.services.crop.ndvi import compute_ndvi, compute_ndvi_stats

router = APIRouter(
    prefix="/api/farms/{farm_id}/fields/{field_id}/ndvi",
    tags=["ndvi"],
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


@router.post("", response_model=NDVIResultOut, status_code=201)
def analyze_ndvi(
    farm_id: int,
    field_id: int,
    body: NDVIResultCreate,
    db: Session = Depends(get_db),
):
    """Compute NDVI from NIR and Red band arrays, store results."""
    _get_field(farm_id, field_id, db)

    nir = np.array(body.nir_band)
    red = np.array(body.red_band)

    if nir.shape != red.shape:
        raise HTTPException(status_code=422, detail="NIR and Red bands must have the same dimensions")
    if nir.ndim != 2:
        raise HTTPException(status_code=422, detail="Band arrays must be 2-dimensional")
    if nir.size == 0:
        raise HTTPException(status_code=422, detail="Band arrays must not be empty")

    ndvi = compute_ndvi(nir, red)
    stats = compute_ndvi_stats(ndvi)

    result = NDVIResult(
        field_id=field_id,
        flight_id=body.flight_id,
        ndvi_mean=stats["ndvi_mean"],
        ndvi_std=stats["ndvi_std"],
        ndvi_min=stats["ndvi_min"],
        ndvi_max=stats["ndvi_max"],
        pixels_total=stats["pixels_total"],
        stress_pct=stats["stress_pct"],
        zones=stats["zones"],
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.get("", response_model=list[NDVIResultOut])
def list_ndvi_results(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    _get_field(farm_id, field_id, db)
    return (
        db.query(NDVIResult)
        .filter(NDVIResult.field_id == field_id)
        .order_by(NDVIResult.analyzed_at.desc())
        .all()
    )


@router.get("/{ndvi_id}", response_model=NDVIResultOut)
def get_ndvi_result(
    farm_id: int,
    field_id: int,
    ndvi_id: int,
    db: Session = Depends(get_db),
):
    _get_field(farm_id, field_id, db)
    result = (
        db.query(NDVIResult)
        .filter(NDVIResult.id == ndvi_id, NDVIResult.field_id == field_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="NDVI result not found")
    return result
