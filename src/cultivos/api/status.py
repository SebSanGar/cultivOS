"""Platform status endpoint — public health check with system overview."""

import time

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from cultivos.auth import get_current_user
from cultivos.db.models import (
    Farm, Field, SoilAnalysis, NDVIResult, ThermalResult, WeatherRecord,
)
from cultivos.db.session import get_db

router = APIRouter(prefix="/api", tags=["status"], dependencies=[Depends(get_current_user)])

_start_time = time.monotonic()


@router.get("/status")
def platform_status(db: Session = Depends(get_db)):
    """Platform overview: counts, latest data timestamps, uptime, and API version."""
    total_farms = db.query(func.count(Farm.id)).scalar() or 0
    total_fields = db.query(func.count(Field.id)).scalar() or 0

    def _latest_ts(model, col):
        val = db.query(func.max(col)).scalar()
        return val.isoformat() if val else None

    latest_data = {
        "soil": _latest_ts(SoilAnalysis, SoilAnalysis.sampled_at),
        "ndvi": _latest_ts(NDVIResult, NDVIResult.analyzed_at),
        "thermal": _latest_ts(ThermalResult, ThermalResult.analyzed_at),
        "weather": _latest_ts(WeatherRecord, WeatherRecord.recorded_at),
    }

    return {
        "api_version": "0.1.0",
        "uptime_seconds": round(time.monotonic() - _start_time, 1),
        "total_farms": total_farms,
        "total_fields": total_fields,
        "latest_data": latest_data,
    }
